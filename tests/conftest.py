"""Pytest configuration and fixtures."""

import pytest

from karabinerpyx import (
    KarabinerConfig,
    LayerStackBuilder,
    Manipulator,
    Profile,
    Rule,
)


@pytest.fixture
def simple_manipulator():
    """A simple key mapping manipulator."""
    return Manipulator("a").to("b")


@pytest.fixture
def simple_rule():
    """A simple rule with one manipulator."""
    return Rule("Test Rule").add(Manipulator("a").to("b"))


@pytest.fixture
def simple_profile():
    """A simple profile with one rule."""
    profile = Profile("Test Profile")
    profile.add_rule(Rule("Test Rule").add(Manipulator("a").to("b")))
    return profile


@pytest.fixture
def simple_layer():
    """A simple layer with basic mappings."""
    return (
        LayerStackBuilder("test_layer", "right_command")
        .map("j", "left_arrow")
        .map("k", "down_arrow")
    )


@pytest.fixture
def simple_config(simple_profile):
    """A simple KarabinerConfig."""
    return KarabinerConfig().add_profile(simple_profile)
