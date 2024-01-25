FROM steamcmd

# install csgo up to date
WORKDIR /home/steam
USER steam
RUN ./steamcmd.sh +login anonymous +force_install_dir csgo/ +app_update 730 validate +quit
