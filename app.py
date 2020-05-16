import os
import torch
import pickle
from flask import Flask, jsonify, request
from sqlalchemy import create_engine, text
from model.net import SenCNN
from model.split import split_morphs
from model.utils import Tokenizer, PadSequence


app = Flask(__name__)
app.config.from_pyfile("config.py")
app.database = create_engine(app.config["DB_URL"], encoding="utf-8", max_overflow=0)

# preprocessor & model
num_classes = app.config["MODEL"]["num_classes"]
max_length = app.config["MODEL"]["length"]

with open("model/checkpoint/vocab.pkl", mode="rb") as io:
    vocab = pickle.load(io)
pad_sequence = PadSequence(length=max_length, pad_val=vocab.to_indices(vocab.padding_token))
tokenizer = Tokenizer(vocab=vocab, split_fn=split_morphs, pad_fn=pad_sequence)

model = SenCNN(num_classes=app.config["MODEL"]["num_classes"],
               vocab=vocab)
ckpt = torch.load("model/checkpoint/best.tar", map_location=torch.device("cpu"))
model.load_state_dict(ckpt["model_state_dict"])
model.eval()


@app.route("/alive_check", methods=["GET"])
def alive_check():
    return "alive", 200


@app.route("/inference", methods=["POST"])
def inference():
    payload = request.json
    sequence = payload.get("comment")
    list_of_tokens = tokenizer.split(sequence)
    list_of_indices = tokenizer.split_and_transform(sequence)

    with torch.no_grad():
        score = model(torch.tensor(list_of_indices).unsqueeze(0))
        max_prob, label = [_.item() for _ in torch.softmax(score, dim=-1).max(dim=-1)]

    record = {"comment": sequence,
              "tokenized_comment": "\u241e".join(list_of_tokens),
              "label": label,
              "max_prob": max_prob}

    app.database.execute(text("""
    INSERT INTO results (comment, tokenized_comment, label, max_prob)
    VALUES (:comment, :tokenized_comment, :label, :max_prob)
    """), record)
    return jsonify(record), 200


if __name__ == "__main__":
    os.system("./run_app.sh")
