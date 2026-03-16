# Reactive Vacuuming Agent (Simple Reflex Agent)

A small PyQt6 simulation of a **simple reflex vacuum agent** that cleans dirt in a room with random obstacles.

Note: This project was developed as coursework for an Artificial Intelligence course at my university.

## Simple Reflex Agent Definition

A simple reflex agent makes decisions based only on the current percept from the environment. It does not use memory of past states or predictions of future consequences. It follows rules of the form: **"if X happens, then do Y."**

## Features

- Random room generation with obstacles (furniture-like blocks)
- Random dirt distribution
- Dark mode interface
- Play/Pause button to control simulation execution
- Regenerate button to create a new random scenario
- Speed input in **cm/s** to model the vacuum velocity
- Reactive movement behavior:
- If current cell is dirty -> clean it
- If front cell is blocked -> move back a little and choose a new direction
- Otherwise -> move forward
- Real-time visual simulation in PyQt6
- Timer showing how long it takes to clean all dirt
- Final summary including simulation time and estimated real-world cleaning time based on user speed

## Distance and Speed Model

- Each grid cell is assumed to represent **1 meter** in the real room.
- The user provides vacuum speed in **centimeters per second (cm/s)**.
- The app uses that speed to control movement pacing and estimate how long the same cleaning path would take in real life.

## Requirements

- Python 3.10+
- PyQt6

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Project Structure

- `main.py`: simulation, reflex rules, and GUI
- `requirements.txt`: dependencies
- `README.md`: project overview
