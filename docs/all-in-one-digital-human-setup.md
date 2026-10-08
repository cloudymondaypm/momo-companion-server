# All-in-One Digital Human Kiosk Setup

Deploy a lightweight full-screen digital-human display and background wake-word service on an x86 computer such as an Intel N100 mini PC. The system automatically opens a kiosk browser at startup and runs microphone-based voice wake-word detection.

These instructions were developed around an Intel N100 Tianhong QN10-100B4 running Ubuntu 24.04 LTS. Adjust networking, audio-device names, paths, and user IDs to fit your own machine.

## Example environment

| Component | Example |
| --- | --- |
| Hardware | Tianhong QN10-100B4 (Intel N100) |
| Operating system | Ubuntu 24.04 LTS |
| Linux user | `xz` (replace with your own user) |
| Network | Wi-Fi with a static LAN IP; Ethernet also works |

## 1. Prepare Ubuntu and networking

Update the operating system with a package mirror appropriate to your location. If you need the original Alibaba Cloud Ubuntu 24.04 mirror, back up and edit your APT sources according to your distro's format. The example below starts from the configured repositories:

```bash
sudo apt update
sudo apt install network-manager -y
sudo systemctl enable --now NetworkManager
```

**Important:** Changing the network profile or static IP can disconnect an SSH session. Prepare local console access before doing so.

Example Wi-Fi connection (replace all sample values):

```bash
sudo nmcli device wifi connect "YOUR_WIFI_SSID" password "YOUR_WIFI_PASSWORD"

# Optional fixed IPv4 address; use your own router and subnet
sudo nmcli connection modify "YOUR_WIFI_SSID" \
  ipv4.addresses "192.168.0.86/24" \
  ipv4.gateway "192.168.0.1" \
  ipv4.dns "8.8.8.8" \
  ipv4.method manual

sudo nmcli connection up "YOUR_WIFI_SSID"
```

## 2. Install a minimal graphical environment

Install X11, Openbox, a mouse-pointer hider, and Chrome. A full GNOME/KDE desktop is not required.

```bash
sudo timedatectl set-timezone Asia/Singapore  # Adjust for your location
sudo apt install net-tools vim alsa-utils pulseaudio -y
sudo apt install --no-install-recommends xserver-xorg x11-xserver-utils xinit openbox unclutter -y

wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb -y
rm google-chrome-stable_current_amd64.deb
```

The upstream instructions also removed `snapd`; that is **optional** and not required for this kiosk. Avoid removing unrelated system packages without a reason.

## 3. Enable automatic login to TTY1

**Security note:** Autologin removes password protection for local console access. Use it only for a trusted, dedicated kiosk device.

Replace `xz` with your Linux username:

```bash
sudo mkdir -p /etc/systemd/system/getty@tty1.service.d/
echo -e "[Service]\nExecStart=\nExecStart=-/sbin/agetty --autologin xz --noclear %I \$TERM" | sudo tee /etc/systemd/system/getty@tty1.service.d/override.conf
sudo systemctl daemon-reload
sudo systemctl set-default multi-user.target
```

## 4. Start the X11 session after login

Append the following to the kiosk user's `~/.bash_profile`:

```bash
cat << 'EOF' >> ~/.bash_profile
if [ -z "$DISPLAY" ] && [ "$(fgconsole)" -eq 1 ]; then
    exec startx
fi
EOF

echo "exec openbox-session" > ~/.xinitrc
```

## 5. Set up the kiosk browser

Create `~/.config/openbox/autostart` for the kiosk user:

```bash
mkdir -p ~/.config/openbox

cat << 'EOF' > ~/.config/openbox/autostart
# Disable screen blanking
xset -dpms
xset s noblank
xset s off

# Hide mouse pointer
unclutter -idle 0.1 -root &

# Restart the kiosk browser if closed
while true; do
    google-chrome \
        --kiosk \
        --no-first-run \
        --no-default-browser-check \
        --disable-infobars \
        --disable-session-crashed-bubble \
        --disable-translate \
        --autoplay-policy=no-user-gesture-required \
        --use-fake-ui-for-media-stream \
        "http://127.0.0.1:8006/index.html"
    sleep 2
done &
EOF
```

The kiosk page will load when the local digital-human runtime starts.

For a managed display, you may also disable Openbox's `Alt+F4` close shortcut, but this reduces local recovery options:

```bash
cp /etc/xdg/openbox/rc.xml ~/.config/openbox/
sed -i '/<keybind key="A-F4">/,/<\/keybind>/d' ~/.config/openbox/rc.xml
```

## 6. Optional boot optimizations

On a dedicated kiosk only, disable waiting for network readiness if it significantly slows boot. This can also allow the browser or services to start before networking is ready:

```bash
sudo systemctl mask systemd-networkd-wait-online.service
sudo systemctl mask NetworkManager-wait-online.service
```

To reduce GRUB boot status output:

```bash
sudo sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT=.*/GRUB_CMDLINE_LINUX_DEFAULT="quiet loglevel=3 systemd.show_status=false vt.global_cursor_default=0"/g' /etc/default/grub
sudo update-grub
```

Set the playback volume, if the mixer exposes a `Master` channel:

```bash
amixer -q sset Master 100% unmute
```

## 7. Install the digital-human wake-word service

### Install Miniconda

```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p "$HOME/miniconda3"
"$HOME/miniconda3/bin/conda" init bash
source ~/.bashrc
rm Miniconda3-latest-Linux-x86_64.sh
```

Make sure your login profile sources `.bashrc` if Conda needs it:

```bash
if ! grep -q '.bashrc' ~/.bash_profile; then
    cat << 'EOF' >> ~/.bash_profile
if [ -f ~/.bashrc ]; then
    . ~/.bashrc
fi
EOF
fi
```

### Create a Python environment

```bash
conda create -n digital-human python=3.10 -y
conda activate digital-human
```

If Conda prompts for terms acceptance, follow its displayed instructions. Typical defaults include:

```bash
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
```

### Copy the application files

From your development machine, upload `main/digital-human` to the kiosk host:

```bash
scp -r main/digital-human/ xz@YOUR_KIOSK_IP:~/digital-human/
```

### Install audio and Python dependencies

```bash
sudo apt install libportaudio2 portaudio19-dev libasound2-plugins -y

cd ~/digital-human/wakeword_runtime
pip install numpy
pip install -r requirements.txt
```

The models are **not included** in the repository. Follow [Digital Human Wake-Word Runtime Setup](digital-human-wakeword.md) to download and configure the model, tokens, and keywords.

## 8. Configure the microphone and Openbox

Start PulseAudio and find the microphone's source name:

```bash
pulseaudio --start
pactl list sources short
```

Set `TARGET_MIC` to the exact source returned by PulseAudio. For a USB camera microphone, it may resemble `alsa_input.usb-SN0002_2K_USB_Camera_...mono-fallback`.

Replace the Openbox autostart file with the following if you need to pin a specific microphone:

```bash
cat << 'EOF' > ~/.config/openbox/autostart
pulseaudio --start
sleep 1

# Replace this with your microphone's actual PulseAudio source ID
TARGET_MIC="YOUR_MICROPHONE_SOURCE"
pactl set-default-source "$TARGET_MIC"
pactl set-source-mute "$TARGET_MIC" 0
pactl set-source-volume "$TARGET_MIC" 100%

xset -dpms
xset s noblank
xset s off
unclutter -idle 0.1 -root &

while true; do
    google-chrome --kiosk --no-first-run --no-default-browser-check \
        --disable-session-crashed-bubble \
        --autoplay-policy=no-user-gesture-required \
        --use-fake-ui-for-media-stream \
        "http://127.0.0.1:8006/index.html"
    sleep 2
done &
EOF
```

## 9. Automatically start the digital-human service

Get the kiosk user's UID:

```bash
id -u "$(whoami)"
```

Create a systemd unit (replace `xz`, UID `1000`, and the file paths as needed):

```ini
[Unit]
Description=Digital Human Runtime
After=network.target sound.target

[Service]
Type=simple
User=xz
Environment=XDG_RUNTIME_DIR=/run/user/1000
Environment=PULSE_SERVER=unix:/run/user/1000/pulse/native
WorkingDirectory=/home/xz/digital-human
ExecStartPre=/bin/sleep 10
ExecStart=/home/xz/miniconda3/envs/digital-human/bin/python start.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Save as `/etc/systemd/system/digital-human.service`. The PulseAudio variables allow the browser and wake-word service to share the microphone in environments configured with that PulseAudio socket.

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now digital-human
```

### Service management

```bash
sudo systemctl start digital-human
sudo systemctl stop digital-human
sudo systemctl restart digital-human
sudo systemctl status digital-human
journalctl -u digital-human -f
```

Restart the kiosk after confirming that all service paths, user IDs, and microphone settings are correct.
