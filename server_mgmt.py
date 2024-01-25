import re
import time
from math import ceil
from typing import List, Dict, IO
import yaml
import docker
import ipaddress

import mysql.connector

# from key import *

with open("config.yml", "r") as config_file:
    config = yaml.load(config_file, Loader=yaml.FullLoader)


def register_server_ebot(servers: List[Dict[str, str]], db_ip: str, tls_config: any) -> None:
    """
    Register a game server to the Ebot server, by adding values to its database.

    :param servers: A list of servers to add
    :param db_ip: The IP of Ebot's DB
    :param tls_config: TLS configuration to use
    """
    containers = []
    csgo_containers = []
    for s in servers:
        client = docker.DockerClient(
            base_url="unix://var/run/docker.sock", tls=tls_config
        )
        containers.extend(client.containers.list("all"))
        csgo_containers.extend(
            c for c in containers if c.attrs["Config"]["User"] == "steam"
        )

    cnx = mysql.connector.connect(
        user="ebotv3", password="ebotv3", host=db_ip, database="ebotv3"
    )
    cursor = cnx.cursor()
    try:
        cursor.execute("delete from servers where id!=-1")
    except:
        print("truncate failed")
    try:
        add_server = (
            "INSERT INTO servers"
            "(ip, rcon, hostname, tv_ip, created_at, updated_at)"
            "values(%s,%s,%s,%s,'2017-12-17 00:00:00','2017-12-17 00:00:00')"
        )
        stvp = re.compile("STV_PORT")
        hostp = re.compile("HOST_PORT")
        ipp = re.compile("IP")
        for i in csgo_containers:
            for y in i.attrs["Config"]["Env"]:
                if stvp.search(y):
                    stvport = re.split("=", y)[1]
                if hostp.search(y):
                    hostport = re.split("=", y)[1]
                if ipp.search(y):
                    ip = re.split("=", y)[1]
            name = i.attrs["Name"]
            data_server = (
                "{}:{}".format(ip, hostport),
                "notbanana",
                name,
                "{}:{}".format(ip, stvport),
            )
            cursor.execute(add_server, data_server)
            cnx.commit()
        cursor.close()
        cnx.close()
    except:
        print("insertion failed")


def deploy_csgoserver(
        nb_csgo: int,
        servers: List[Dict[str, str]],
        ebot_ip: str,
        image: str,
        tls_config: any,
        topo: IO
) -> None:
    """
    Deploy csgo containers over physical servers.

    :param nb_csgo: Number of container to deploy
    :param servers: List of physical servers on which the containers will be deployed
    :param ebot_ip: IP address of ebot (#FIXME confirm with original author)
    :param image: Name of the docker image to deploy
    :param tls_config: TLS configuration to use
    :param topo: File descriptor to the topology file

    """

    ip = ipaddress.ip_address(ebot_ip)
    hostport = 27015
    clientport = hostport + nb_csgo
    stvport = clientport + nb_csgo
    hostname = "csgoinsalan"
    for y in range(0, len(servers)):
        for i in range(
                int(ceil(nb_csgo / len(servers)) * y),
                int(ceil(nb_csgo / len(servers)) * (y + 1)),
        ):
            ip = ipaddress.ip_address(ip + 1)
            client = docker.APIClient(
                base_url="unix://var/run/docker.sock", tls=tls_config
            )
            container = client.create_container(
                image,
                detach=True,
                hostname=hostname,
                host_config=client.create_host_config(
                    extra_hosts={hostname: servers[y]},
                    restart_policy={"Name": "always"},
                    network_mode="host",
                ),
                environment={
                    "IP": "{}".format(servers[y]),
                    "CSGO_HOSTNAME": "csgo-server-{}".format(i),
                    "CSGO_PASSWORD": "",
                    "RCON_PASSWORD": "notbanana",
                    "STEAM_ACCOUNT_TOKEN": config["csgo"]["tokens"][i] if len(config["csgo"]["tokens"]) > i else "",
                    # FIXME : check before anything instead of failing midway
                    "HOST_PORT": str(hostport + i),
                    "CLIENT_PORT": str(clientport + i),
                    "STV_PORT": str(stvport + i),
                },
                name="csgo-servers-{}".format(i),
            )
            client.start(container)
            topo.write("csgo-servers-{};{};{}\n".format(i, str(ip), client.base_url))
