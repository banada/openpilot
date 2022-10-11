#!/usr/bin/env python3
import time
import threading
from flask import Flask

import cereal.messaging as messaging

app = Flask(__name__)
pm = messaging.PubMaster(['testJoystick'])

index = """
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"></meta>
  <script src="https://github.com/bobboteck/JoyStick/releases/download/v1.1.6/joy.min.js"></script>
  <link href="https://unpkg.com/tailwindcss@^1.0/dist/tailwind.min.css" rel="stylesheet">
  <script>
  </script>
</head>
<body>
<div id="joyDiv" style="width:100%;height:100%"></div>
<div id="info" class="flex flex-col justify-between items-center mt-4 mx-4 text-center">
  <div class="text-4xl">
    Speed Mode:
    <span id="speedMode"></span>
  </div>
  <div class="text-4xl">
    Turn:
    <span id="turn"></span>
  </div>
  <div class="text-4xl">
    Direction:
    <span id="direction"></span>
  </div>
</div>
<script type="text/javascript">
  const REFRESH_INTERVAL = 50;

  const GAMEPAD_BUTTONS = {
    TRIGGER_LEFT: 6,
    TRIGGER_RIGHT: 7,
    DPAD_UP: 12,
    DPAD_DOWN: 13
  }
  const SPEED_MODE = {
    LOW: 0,
    MEDIUM: 1,
    HIGH: 2
  }
  const SPEED_SCALE = {
    LOW: 0.33,
    MEDIUM: 0.66,
    HIGH: 1
  }
  let currentSpeedMode;
  let buttonLock;
  let globalY = 0;
  let speedScale;

  function isUndef(val) {
    return ((val === undefined) || (val === null));
  }

  function checkButtonLock(button, evt) {
    const buttonName = Object.keys(GAMEPAD_BUTTONS).find(b => GAMEPAD_BUTTONS[b] === button);
    // Release lock
    if (!evt.pressed) {
      buttonLock = null;
    }
  }

  function handleGamepadButtonPress(button, evt) {
    const activeButton = Object.keys(GAMEPAD_BUTTONS)[button];
    if (activeButton) {
    }
    const directionEl = document.getElementById('direction');

    switch (button) {
      // Increase speed mode
      case GAMEPAD_BUTTONS.DPAD_UP:
        if (!evt.pressed) {
          break;
        }
        buttonLock = button;
        if (currentSpeedMode < SPEED_MODE.HIGH) {
          changeSpeedMode(currentSpeedMode + 1);
        }
        break;
      // Decrease speed mode
      case GAMEPAD_BUTTONS.DPAD_DOWN:
        if (!evt.pressed) {
          break;
        }
        buttonLock = button;
        if (currentSpeedMode > SPEED_MODE.LOW) {
          changeSpeedMode(currentSpeedMode - 1);
        }
        break;
      case GAMEPAD_BUTTONS.TRIGGER_LEFT:
        directionEl.textContent = `REVERSE ${Math.round(evt.value * 100)}%`;
        globalY = -1 * evt.value;
        break;
      case GAMEPAD_BUTTONS.TRIGGER_RIGHT:
        directionEl.textContent = `FORWARD ${Math.round(evt.value * 100)}%`;
        globalY = evt.value;
        break;
      default:
        break;
    }
  }

  function changeSpeedMode(speedMode) {
    currentSpeedMode = speedMode;
    const speedModeEl = document.getElementById('speedMode');
    speedModeEl.textContent = Object.keys(SPEED_MODE)[currentSpeedMode];

    switch (speedMode) {
      case SPEED_MODE.LOW:
        speedScale = SPEED_SCALE.LOW;
        document.body.style.backgroundColor = '#9ae6b4';
        break;
      case SPEED_MODE.MEDIUM:
        speedScale = SPEED_SCALE.MEDIUM;
        document.body.style.backgroundColor = '#fefcbf';
        break;
      case SPEED_MODE.HIGH:
        speedScale = SPEED_SCALE.HIGH;
        document.body.style.backgroundColor = '#feb2b2';
        break;
    }
  }

  document.addEventListener('DOMContentLoaded', function() {
    changeSpeedMode(SPEED_MODE.LOW)
  });

  // Set up gamepad handlers
  let gamepad = null;
  window.addEventListener("gamepadconnected", function(e) {
    console.log('gamepad connected');
    gamepad = e.gamepad;
    // Hide joystick
    const joyEl = document.getElementById('joyDiv');
    joyEl.style.display = 'none';
  });
  window.addEventListener("gamepaddisconnected", function(e) {
    console.log('gamepad disconnected');
    gamepad = null;
    // Show joystick
    const joyEl = document.getElementById('joyDiv');
    joyEl.style.display = 'block';
  });

  // Create JoyStick object into the DIV 'joyDiv'
  var joy = new JoyStick('joyDiv');

  // Joystick control
  const turnEl = document.getElementById('turn');
  setInterval(function(){
    var x = -joy.GetX()/100;
    var y = -joy.GetY()/100;
    if (x === 0 && y === 0 && gamepad !== null) {
      let gamepadstate = navigator.getGamepads()[gamepad.index];
      x = -gamepadstate.axes[0];
      x = x.toFixed(2);
      if (x < 0) {
        turnEl.textContent = `RIGHT ${Math.round(-x * 100)}%`;
      } else {
        turnEl.textContent = `LEFT ${Math.round(x * 100)}%`;
      }

      // Neither trigger pressed, set zero longitudinal
      let hasLongitudinal = true;
      if (!gamepadstate.buttons[GAMEPAD_BUTTONS.TRIGGER_LEFT].pressed && !gamepadstate.buttons[GAMEPAD_BUTTONS.TRIGGER_RIGHT].pressed) {
        hasLongitudinal = false;
      }
      gamepadstate.buttons.forEach((button, idx) => {
        if (!isUndef(buttonLock) && (idx === buttonLock)) {
          checkButtonLock(idx, button);
        } else if (button.pressed) {
          handleGamepadButtonPress(idx, button);
        }
      });

      if (hasLongitudinal) {
        y = globalY * speedScale;
        y = -y.toFixed(2);
      } else {
        const directionEl = document.getElementById('direction');
        directionEl.textContent = `IDLE`;
        y = 0;
      }
    }

    let xhr = new XMLHttpRequest();
    xhr.open("GET", "/control/"+x+"/"+y);
    xhr.send();
  }, REFRESH_INTERVAL);
</script>
"""

@app.route("/")
def hello_world():
  return index

last_send_time = time.monotonic()
@app.route("/control/<x>/<y>")
def control(x, y):
  global last_send_time
  x,y = float(x), float(y)
  x = max(-1, min(1, x))
  y = max(-1, min(1, y))
  dat = messaging.new_message('testJoystick')
  dat.testJoystick.axes = [y,x]
  dat.testJoystick.buttons = [False]
  pm.send('testJoystick', dat)
  last_send_time = time.monotonic()
  return ""

def handle_timeout():
  while 1:
    this_time = time.monotonic()
    if (last_send_time+0.5) < this_time:
      #print("timeout, no web in %.2f s" % (this_time-last_send_time))
      dat = messaging.new_message('testJoystick')
      dat.testJoystick.axes = [0,0]
      dat.testJoystick.buttons = [False]
      pm.send('testJoystick', dat)
    time.sleep(0.1)

def main():
  threading.Thread(target=handle_timeout, daemon=True).start()
  app.run(host="0.0.0.0")

if __name__ == '__main__':
  main()
