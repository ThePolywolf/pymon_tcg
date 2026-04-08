Loading/Saving data:
- polars

Simulation:
- Concurrency
- JAX / Vectorized (NumPy, or ECS/Esper)

## Hybrid Architecture

### 1. Core
Shared logic, writes rules of the game (damage calc, energy management)

Python/Rust:

- Input: A "State" object + an "Action" (e.g., Play Card #3).
- Output: A new "State" object.
- Why: This ensures that the AI and the Human are playing the exact same game rules.

### 2. Simulation Driver (JAX/NumPy/Multiprocessing)
Neural network training and fast sims

- Batching: Running multiple games at once (2 ** x = 1024default)
- AI Training: RL algorithm observing vector state to pick actions

### 3. Interactive Driver (ECS/UI)
User-played battles, Core wrapped in ECS framework

- Visuals
- Input

