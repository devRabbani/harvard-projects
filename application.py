import os
import datetime
from flask import Flask, render_template, redirect, jsonify, request, url_for, session
from flask_socketio import SocketIO, emit, send
from flask_session import Session
from channels import Channel

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

socketio = SocketIO(app)
Session(app)
channels = []

@app.route("/")
def index():
    """Try to render with the Display Name form session, but if there's not anyone yet just render simpler"""
    try:
        return render_template("index.html", name=session["name"], lastChannel=session["lastChannel"], channels=channels)
    except KeyError:
        try:
            return render_template("index.html", name=session["name"], channels=channels)
        except KeyError:
            return render_template("index.html", channels=channels)

@app.route("/name", methods=["POST"])
def name():
    name = request.form.get("name")
    """If Display Name not empty create and remember in session"""
    if name is not '':
        session["name"] = name
        return jsonify({"success": True, "name": name})
    else:
        return jsonify({"success": False})

@app.route("/lastChannel", methods=["POST"])
def lastChannel():
    """Remember Last Channel visited in Session"""
    channel = request.form.get("lastChannel")
    session["lastChannel"] = channel
    return '', 204

@app.route("/channel", methods=["POST"])
def channel():
    channel = request.form.get('channel')
    # If element already exist, NOT create another with the same name
    for elem in channels:
        if channel in elem.name:
            return jsonify({"success": False})
    # If no channel named the same, then create a new one
    newChannel = Channel(channel)
    channels.append(newChannel)
    # Create a dictionary for every object so then can be tranformed easily into JSON objects
    channelsFeed = []
    for object in channels:
        channelsFeed.append(object.__dict__)
    return jsonify({"success": True, "channel": channel, "channels": channelsFeed})

@app.route("/delete", methods = ["POST"])
def delete():
    channel = request.form.get("channel")
    message = request.form.get("message")

    for may_channel in channels:
        if may_channel.name == channel:
            for may_message in may_channel.messages:
                if may_message["message"] == message:
                    del(may_channel.messages[may_channel.messages.index(may_message)])
    return '', 204

@socketio.on("sendMessage")
def chat(data):
    channel = data["channel"]
    message = data["message"]
    # Check all existing channels seeking for the same name
    for checkChannel in channels:
        # If exist then append the new message else emit a Not success message
        if checkChannel.name == channel:
            time = '{:%H:%M:%S}'.format(datetime.datetime.now())
            sender = session["name"]
            checkChannel.newMessage(message, sender, channel, time)

            last_message = checkChannel.messages[-1]
            emit("update", last_message, broadcast=True)
            return
    emit("update", 'Not success', broadcast=True)

@socketio.on("update")
def conect(data):
    channel = data["channel"]
    #Checking for an existing channel with that same name
    for checkChannel in channels:
        # If exist, charge all old messages stored there and emit
        if checkChannel.name == channel:
            oldMessages = checkChannel.messages
            name = session["name"]
            emit("updateChat", (oldMessages, name), broadcast=True)
            return
    # Else, emit a notFound message
    emit("updateChat", 'notFound', broadcast=True)

if __name__ == '__main__':
    socketio.run(app)
