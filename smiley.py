import matplotlib.pyplot as plt
import numpy as np

# Erstellen der Figur und des Achsensystems
fig, ax = plt.subplots()

# Kreis für das Gesicht
face = plt.Circle((0.5, 0.5), 0.44, color='yellow', ec='black', linewidth=3)
ax.add_patch(face)

# Augen
left_eye = plt.Circle((0.35, 0.65), 0.05, color='black')
right_eye = plt.Circle((0.65, 0.65), 0.05, color='black')
ax.add_patch(left_eye)
ax.add_patch(right_eye)

# Mund (Bogen für ein Lächeln)
theta = np.linspace(np.pi / 6, 5 * np.pi / 6, 100)
x = 0.5 + 0.2 * np.cos(theta)
y = 0.35 - 0.1 * np.sin(theta)
ax.plot(x, y, color='black', linewidth=3)

# Einstellen der Anzeigeoptionen
ax.set_aspect('equal')
plt.axis('off')
plt.show()
