# Galton Board

A Galton board is a physical device invented by Sir Francis Galton in the 1870s to demonstrate how the binomial distribution approximates the normal distribution.

## How It Works

A ball is dropped from the top and hits a series of pegs arranged in a triangular grid. At each peg, the ball deflects randomly left or right with equal probability. After passing through all rows of pegs, the ball falls into one of the bins at the bottom.

With enough balls, the counts in each bin form a bell curve — a visual proof of the **Central Limit Theorem**.

## This Simulation

- **1000 balls** dropped through **12 rows** of pegs
- Each ball's path is animated in real time
- A histogram builds up as balls land in their bins
- A theoretical normal curve overlay appears as the distribution takes shape

## Setup
```bash
git clone https://github.com/villoslado/GaltonBoard.git
cd GaltonBoard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python galton_board.py
```
