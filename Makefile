# name of your application
APPLICATION = project_digi

# If no BOARD is found in the environment, use this default:
#BOARD ?= nrf52840dk
BOARD ?= native

USEMODULE += netdev_default
USEMODULE += auto_init_gnrc_netif
USEMODULE += xtimer  

USEMODULE += gnrc_ipv6_default
USEMODULE += gnrc_icmpv6_echo

# SAUL Sensor Actuator Uber Layer 
USEMODULE += saul_default

CFLAGS += -Wno-unused-parameter
CFLAGS += -Wno-unused-function
CFLAGS += -Wno-unused-variable

# Required for DHT 11 Humidity Sensor
USEMODULE += dht
USEMODULE += periph_gpio
USEMODULE += fmt

# Required by GCoAP
USEMODULE += od
USEMODULE += fmt
USEMODULE += netutils
USEMODULE += random

# Add also the shell, some shell commands
USEMODULE += shell
USEMODULE += shell_cmds_default
USEMODULE += ps
USEMODULE += uri_parser

GCOAP_ENABLE_DTLS ?= 1
ifeq (1,$(GCOAP_ENABLE_DTLS))
  # Required by DTLS. Currently, only tinyDTLS is supported by sock_dtls.
  USEPKG += tinydtls
  USEMODULE += sock_dtls
  USEMODULE += tinydtls_sock_dtls
  USEMODULE += gcoap_dtls 
  # tinydtls needs crypto secure PRNG
  USEMODULE += prng_sha1prng
endif

# This has to be the absolute path to the RIOT base directory:
RIOTBASE ?= $(RIOTBASE)

# Comment this out to disable code in RIOT that does safety checking
# which is not needed in a production environment but helps in the
# development process:
DEVELHELP ?= 1

# Change this to 0 show compiler invocation lines by default:
QUIET ?= 1

# Default Channel has to be the same as on the Border Router
DEFAULT_CHANNEL = 14

include $(RIOTMAKE)/default-radio-settings.inc.mk

include $(RIOTBASE)/Makefile.include