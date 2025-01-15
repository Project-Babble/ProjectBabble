![Babble Logo](https://github.com/Project-Babble/ProjectBabble/blob/6f09c3b091bff996a1ec543e1ac1050a15a636af/Babble.png)

<h3 align="center">
Project Babble is an open-source mouth tracking project designed to work with any VR headset. We strive to make our models robust to different lighting, cameras, image qualities and facial structures!
</h3>

## Interested in selling babble hardware?
By defualt Project Babble is under a non-commerical license! Please contact us at projectbabblevr@gmail.com to obtain a commercial license!

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Links](#links)
  
## Features
- 100% open-source! 🌟
- Fast and robust! 🚀
- Works with existing blendshape standards! ⚙️
- Constantly updated and modified! 🔧

## Installation
### Windows
Head to the releases section and [download the latest installer](https://github.com/Project-Babble/ProjectBabble/releases/latest).

### Linux
Install `git`, `curl` and a version of `python` greater than `3.8` for your distro. 

Then, copy paste and run the following script into the terminal of your choice:

```bash
bash -c "$(curl -fsSL https://gist.githubusercontent.com/dfgHiatus/a92a3caae24c1bfab1c7544537a654c5/raw/fc30aa550c3c7aa83c37a72168e75ef92388e39b/project-babble-install.sh)"
```

Once it's finished installing, you can update and run the Babble app by typing `babble-app` into your terminal.

*You should also be able to run the Windows executable through Wine!*

#### Notes:
If you receive a `["Error listing UVC devices on Linux ... No such file or directory"]` when choosing/changing your camera, you'll need to install video4linux (`v4l-utils`) for your distro.

For Ubuntu or other distros with apt:
```bash
sudo apt-get install v4l-utils
```

If you receive a `ModuleNotFoundError: No module named 'tkinter'` error message on run, you'll need to install `tkinter` for your distro.

For Ubuntu or other distros with apt:
```bash
sudo apt-get install python3-tk
```
For Fedora:
```bash
sudo dnf install python3-tkinter
```

You can read more about this [here](https://stackoverflow.com/questions/25905540/importerror-no-module-named-tkinter).

## Usage 
We have integrations for [VRChat](https://docs.babble.diy/docs/software/integrations/vrc), [Resonite](https://docs.babble.diy/docs/software/integrations/resonite) and [ChilloutVR](https://docs.babble.diy/docs/software/integrations/chilloutVR)!

Looking for something else? Check out our [documentation](https://docs.babble.diy/)!

## Links
- [Our Discord](https://discord.gg/XAMZmjBktk)
- [Our Twitter](https://x.com/projectBabbleVR)
- [Wandb Runs](https://wandb.ai/summerai/ProjectBabble)
