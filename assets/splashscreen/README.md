# Splash Screen

Custom splash screen voor Raspberry Pi boot/shutdown.
Wordt automatisch geïnstalleerd met ./install.sh

## Vereisten

- **Bestandsnaam:** `splash_1024x614.png`
- **Formaat:** PNG
- **Huidige resolutie:** 1024x614 (aangepast voor dit project)
- **Aspect ratio:** Behoud aspect ratio van je scherm

## Installatie

```bash
./install/install_splash.sh
```

Het script:
1. Maakt backup van originele splash screen
2. Kopieert `splash.png` naar `/usr/share/plymouth/themes/pix/`
3. Vraagt sudo wachtwoord
4. Toont instructies voor testen

## Testen

Reboot je Raspberry Pi:
```bash
sudo reboot
```

De splash screen verschijnt tijdens boot en shutdown.

## Origineel herstellen

```bash
sudo cp /usr/share/plymouth/themes/pix/splash.png.backup /usr/share/plymouth/themes/pix/splash.png
sudo reboot
```

## Tips voor een goede splash screen

- Gebruik een donkere achtergrond (zwart werkt goed)
- Houd belangrijke elementen gecentreerd
- Test op je scherm resolutie
- PNG formaat voor transparantie support
- Maximaal 1-2 kleuren voor clean look
