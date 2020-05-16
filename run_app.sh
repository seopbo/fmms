#!/usr/bin/env zsh

args=$1

case $1 in
  run)
    echo "run app"
    # flask 웹 어플리케이션은 development 모드로 run
    export FLASK_ENV=development # flask가 실행되는 개발 스테이지, development로 정해놓으면 debug mode 실행
    export FLASK_app=app.py
    screen -dmS flask-server zsh -c "source ~/.zshrc && pyenv activate fmms && flask run"
    ;;
  kill)
    echo "kill app"
    screen -S flask-server -X quit
    ;;
esac