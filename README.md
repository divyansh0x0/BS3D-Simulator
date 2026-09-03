# BS3D-Simulator

## Architecture
The project is split into 3 modules:
1. Frontend
2. Backend
3. Core

These modules must not depend on each other and should remain strictly decoupled.

### 1. Frontend Architecture
The frontend will be built using [Flet](https://flet.dev/). It needs to be object-oriented and modular to keep the codebase organized and easy to maintain. We will use `PlotlyChart` in this layer to render all the graphs.

### 2. Backend Architecture
To maximize learning, the backend physics solver will rely entirely on [NumPy](https://numpy.org/), no other heavy math or engineering libraries unless absolutely required.

### 3. Core Architecture
This module will house shared utilities, common data structures, and miscellaneous functionalities that don't strictly belong to the math solver or the UI. 

## Project Goals
1. Build a physics engine that can solve for Point Loads, Uniformly Distributed Loads (UDL), and Uniformly Varying Loads (UVL).
2. Keep the architecture modular so that updating one system doesn't force a massive rewrite of the others.
3. Build a clean, intuitive UI with good UX so users can figure it out without needing to read a manual.

## Task List

**Frontend:**
- [ ] Implement the selection screen for I-Beam, Circular Beam, and Rectangular Beam.
- [ ] Add on-the-fly customization for the selected beam.
- [ ] Build the view layout for the matplotlib graphs.
- [ ] Create input forms for the applied loads.
- [ ] Create output views for the SFD, BMD, Shear Stress, and Bending Stress graphs.

**Backend:**
- [ ] Write the solver logic for the different load types.
- [ ] Write the solver that outputs data arrays for the SFD and BMD.
- [ ] Write the solver that calculates arrays for Shear Stress and Bending Stress.

## Note to Contributors
Do not commit code you cannot explain. Every contributor should understand how both the frontend and backend work. Using AI is fine, but keep it minimal—use it strictly as a tool to avoid bloated code and unnecessary complexity, not to write logic you don't understand.