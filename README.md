![Babble Logo](https://github.com/Project-Babble/ProjectBabble/blob/6f09c3b091bff996a1ec543e1ac1050a15a636af/Babble.png)

<h3 align="center">
Project Babble is a source first mouth tracking project designed to work with any VR headset. We strive to make our models robust to different lighting, cameras, image qualities and facial structures!
</h3>

## Interested in selling babble hardware?
By defualt Project Babble is under a non-commerical license! Please contact us at projectbabblevr@gmail.com to obtain a commercial license!

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Links](#links)
  
## Features
- 100% free and source available! 🌟
- Fast and robust! 🚀
- Works with existing blendshape standards! ⚙️
- Constantly updated and modified! 🔧

## Installation
### Windows
Head to the releases section and [download the latest installer](https://github.com/Project-Babble/ProjectBabble/releases/latest).

### MacOS and Linux
Install `git`, `curl` and a version of `python` (between `3.10` and `3.12`) for your distro.

Then, copy paste and run the following script into the terminal of your choice:

#### For the latest commit:

```bash
bash -c "$(curl -fsSL https://gist.githubusercontent.com/dfgHiatus/e1bce63cd6be1e8645c3b3adfd5b71a6/raw/26561da3b2bcf738f580176229e4853c18ddf554/project-babble-installer-latest.sh)"
```

#### For the latest tagged release:

```bash
bash -c "$(curl -fsSL https://gist.githubusercontent.com/dfgHiatus/a92a3caae24c1bfab1c7544537a654c5/raw/63573d5c882b4152c9434b9dd4bc888573fe9e98/project-babble-installer-tagged.sh)"
```

Once it's finished installing, you can update and run the Babble app by typing `babble-app` into your terminal. You *should* also be able to run the Windows executable through Wine!

*Sometimes, the update script can error out if there are updates to pull from git. Fear not, re-rerunning the script in most cases fixes things.*

#### Notes on Linux:

##### KDE Plasma

If your GUI window shows just the top row of radio buttons, set a resolution for the Babble App manually in KDE's Window Settings. 800x600y is a good starting point with plenty of empty space.

---

##### v4l2/v4l-linux

If you receive a `["Error listing UVC devices on Linux ... No such file or directory"]` when choosing/changing your camera, you'll need to install video4linux (`v4l-utils`) for your distro.

For Ubuntu or other distros with apt:
```bash
sudo apt-get install v4l-utils
```

---

##### tkinter

If you receive a `ModuleNotFoundError: No module named 'tkinter'` error message on run, you'll need to install `tkinter` for your distro.

For Ubuntu or other distros with apt:
```bash
sudo apt-get install python3-tk
```
For Fedora:
```bash
sudo dnf install python3-tkinter
```
For MacOS:
```bash
brew install python-tk
```

You can read more about this [here](https://stackoverflow.com/questions/25905540/importerror-no-module-named-tkinter) and [here](https://stackoverflow.com/questions/36760839/why-does-python-installed-via-homebrew-not-include-tkinter).

---

##### udev

If you have trouble connecting to your Babble Board (IE being denied permission to access it), you will need to set up and configure [udev](https://docs.platformio.org/en/latest/core/installation/udev-rules.html) rules.

## Usage 
We have integrations for [VRChat](https://docs.babble.diy/docs/software/integrations/vrc), [Resonite](https://docs.babble.diy/docs/software/integrations/resonite) and [ChilloutVR](https://docs.babble.diy/docs/software/integrations/chilloutVR)!

Looking for something else? Check out our [documentation](https://docs.babble.diy/)!

## Links
- [Our Discord](https://discord.gg/XAMZmjBktk)
- [Our Twitter](https://x.com/projectBabbleVR)
- [Wandb Runs](https://wandb.ai/summerai/ProjectBabble)
