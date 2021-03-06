# The Reinforcement Learning Toybox [![Build Status](https://travis-ci.com/toybox-rs/Toybox.svg?token=wqGZxUYsDSPaq1jz2zn6&branch=master)](https://travis-ci.com/toybox-rs/Toybox)

A set of games designed for testing deep RL agents.

If you use this code, or otherwise are inspired by our white-box testing approach, please cite our [NeurIPS workshop paper](https://arxiv.org/abs/1812.02850):

```
@inproceedings{foley2018toybox,
  title={{Toybox: Better Atari Environments for Testing Reinforcement Learning Agents}},
  author={Foley, John and Tosch, Emma and Clary, Kaleigh and Jensen, David},
  booktitle={{NeurIPS 2018 Workshop on Systems for ML}},
  year={2018}
}
```

## How accurate are your games?

[Watch four minutes of agents playing each game](https://www.youtube.com/watch?v=spx_YQQW1Lw). Both ALE implementations and Toybox implementations have their idiosyncracies, but the core gameplay and concepts have been captured. Pull requests always welcome to improve fidelity.

## Where is the actual Rust code?

The rust implementations of the games have moved to a different repository: [toybox-rs/toybox-rs](https://github.com/toybox-rs/toybox-rs)

## Where is the Python code?

Go into the ``ctoybox`` directory, and use the ``start_python`` script. This will help set up your path and virtual-environments.

## Play the games (using pygame)

    pip install ctoybox pygame
    python -m ctoybox.human_play breakout
    python -m ctoybox.human_play amidar
    python -m ctoybox.human_play space_invaders

## Run the tests

1. Navigate to `ctoybox`. 
2. Run `pip3 install -r REQUIREMENTS.txt`
3. Run `PYTHONPATH=baselines:toybox python3 -m unittest toybox.sample_tests.test_${GAME}.${TEST_NAME}`


## Python

Tensorflow, OpenAI Gym, OpenCV, and other libraries may or may not break with various Python versions. We have confirmed that the code in this repository will work with the following Python versions:

* 3.5

## Get starting images for reference from ALE / atari_py

`./scripts/utils/start_images --help` 
