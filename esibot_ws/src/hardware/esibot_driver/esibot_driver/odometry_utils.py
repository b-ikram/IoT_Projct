import math

class OdometryComputer:
    def __init__(self, wheel_radius, wheel_separation, ticks_per_rev):
        # Paramètres du robot (issus du .yaml)
        self.R = wheel_radius           # Rayon de la roue (m)
        self.L = wheel_separation       # Entraxe entre les roues (m)
        self.TPR = ticks_per_rev        # Résolution de l'encodeur (ticks/tour)
        
        # État du robot (x, y en mètres, th en radians)
        self.x = 0.0
        self.y = 0.0
        self.th = 0.0
        
        # Mémoire pour calculer le Δ (différence) entre deux lectures
        self.last_left_ticks = None
        self.last_right_ticks = None

    def update(self, left_ticks, right_ticks):
        """
        Calcule la nouvelle position. 
        Appelée à chaque fois que l'ESP32 envoie des données (Tâche 25).
        """
        # Initialisation : on enregistre juste la position de départ
        if self.last_left_ticks is None:
            self.last_left_ticks = left_ticks
            self.last_right_ticks = right_ticks
            return self.x, self.y, self.th

        # 1. Calcul du déplacement des encodeurs (Δticks)
        d_left_ticks = left_ticks - self.last_left_ticks
        d_right_ticks = right_ticks - self.last_right_ticks
        
        # 2. Conversion en distance linéaire (mètres)
        # Formule : (Δticks / TPR) * 2 * PI * R
        d_left_m = (d_left_ticks / self.TPR) * (2 * math.pi * self.R)
        d_right_m = (d_right_ticks / self.TPR) * (2 * math.pi * self.R)
        
        # 3. Calcul du mouvement du centre du robot (ds) et rotation (dth)
        ds = (d_right_m + d_left_m) / 2.0
        dth = (d_right_m - d_left_m) / self.L  #Transforme l'écart entre les roues en un angle (la rotation).
        
        # 4. Intégration de la position (Trigonométrie)
        # On utilise th + dth/2 pour plus de précision dans les courbes
        self.x += ds * math.cos(self.th + dth / 2.0)
        self.y += ds * math.sin(self.th + dth / 2.0)
        self.th += dth
        
        # Garder en mémoire pour le prochain calcul
        self.last_left_ticks = left_ticks
        self.last_right_ticks = right_ticks
        
        return self.x, self.y, self.th