# mypy: disable-error-code="attr-defined"
# pyright: reportAttributeAccessIssue=false

from pathlib import Path

import trimesh

filename = 'conveyor_plate.stl'
extras = 'sliding_plate/collision'
package_name = 'mechanism_description'

ws_dir = 'dobot_ws'

cwd: Path = Path(__file__).parent

file: Path = cwd / ws_dir/'src'/package_name / 'meshes' / extras / filename


mesh: trimesh.Geometry = trimesh.load(file)

# Check mesh
print("Watertight:", mesh.is_watertight)
print("Volume:", mesh.volume)

# Material density: kg/m³
density = 780.0

mass = mesh.volume * density

# Center of mass
com = mesh.center_mass

# Inertia about the mesh center of mass
inertia = mesh.moment_inertia * density

print("Mass:", mass, "kg")
print("COM:", com)
print("Inertia:")
print(inertia)
