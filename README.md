# pyenvertech-evt800 library

[![Workflow Status](https://github.com/daniel-bergmann-00/pyenvertech-evt800/actions/workflows/main.yml/badge.svg?branch=master)](https://github.com/daniel-bergmann-00/pyenvertech-evt800/actions)

Envertech EVT800 library for Python 3. The library was created
to integrate Envertech EVT800 inverters with HomeAssistant

See <https://www.envertec.com/> for more information on the Envertech solar
inverters

## Example usage

See [example.py](./example.py) for a basic usage and tests

## Home Assistant (TODO)

The Home Assistant Envertech EVT800 documentation can be found
[here](https://www.home-assistant.io/components/TODO)

> ---
>
> **This library uses the TCP-Server of the EVT-800 device.**
> 
> **If you can access your EVT-800 via your browser, this might work for you.**
>
> ---

### How to debug this addon

1. Ensure you can access your EVT-800 from your browser

To enable detailed logging in Home Assistant, you can add the following to your configuration

```yaml
logger:
  default: info
  logs:
    homeassistant.components.pyenvertechevt800: debug
    pyenvertechevt800: debug
```
## Technical Info

see: https://github.com/brandon1024/OpenEVT
