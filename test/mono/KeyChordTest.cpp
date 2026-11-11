#include <gtest/gtest.h>

#include "mono/KeyChord.h"

namespace {

constexpr unsigned NONE = 0;
constexpr unsigned UP = mono::KeyChord::KEY_UP;
constexpr unsigned BOTH = mono::KeyChord::BOTH_KEYS;

struct Frame {
  bool powerHeld;
  unsigned keys;
  unsigned long heldMs;
};

// Feeds one frame and returns the chord after it.
const mono::KeyChord& step(mono::KeyChord& chord, const Frame frame) {
  chord.update(frame.powerHeld, frame.keys, frame.heldMs);
  return chord;
}

// Holds both keys until the chord fires, then lets go of both in the next frame.
void chordAndLetGo(mono::KeyChord& chord) {
  step(chord, {false, BOTH, 0});
  step(chord, {true, BOTH, 650});
  step(chord, {false, NONE, 700});
  step(chord, {false, NONE, 700});
  step(chord, {false, NONE, 700});
}

TEST(KeyChord, StartsInactive) {
  const mono::KeyChord chord;
  EXPECT_FALSE(chord.wasPressed());
  EXPECT_FALSE(chord.isActive());
  EXPECT_FALSE(mono::homeChord().isActive());
}

TEST(KeyChord, PowerClickIsNotTheChord) {
  mono::KeyChord chord;
  EXPECT_FALSE(step(chord, {true, NONE, 0}).isActive());
  EXPECT_FALSE(step(chord, {false, NONE, 12}).isActive());
  EXPECT_FALSE(chord.wasPressed());
}

// A slow frame after the click's press must not turn its release into a chord.
TEST(KeyChord, LateClickReleaseIsNotTheChord) {
  mono::KeyChord chord;
  step(chord, {true, NONE, 0});
  EXPECT_FALSE(step(chord, {false, NONE, 2000}).isActive());
  EXPECT_FALSE(chord.wasPressed());
}

// One key held alone gives Back or Confirm, never the chord.
TEST(KeyChord, OneKeyIsNotTheChord) {
  mono::KeyChord chord;
  step(chord, {false, UP, 0});
  EXPECT_FALSE(step(chord, {false, UP, 0}).isActive());
  EXPECT_FALSE(step(chord, {false, NONE, 0}).isActive());
}

TEST(KeyChord, HeldTimeBoundary) {
  for (const unsigned long heldMs : {0UL, 649UL}) {
    mono::KeyChord chord;
    step(chord, {true, BOTH, heldMs});
    EXPECT_FALSE(chord.wasPressed()) << heldMs;
    EXPECT_FALSE(chord.isActive()) << heldMs;
  }
  for (const unsigned long heldMs : {650UL, 2000UL}) {
    mono::KeyChord chord;
    step(chord, {true, BOTH, heldMs});
    EXPECT_TRUE(chord.wasPressed()) << heldMs;
    EXPECT_TRUE(chord.isActive()) << heldMs;
  }
}

TEST(KeyChord, FiresOnceWhileHeld) {
  mono::KeyChord chord;
  EXPECT_TRUE(step(chord, {true, BOTH, 650}).wasPressed());
  EXPECT_FALSE(step(chord, {true, BOTH, 900}).wasPressed());
  EXPECT_TRUE(chord.isActive());
}

// Both keys up in one frame: the chord covers that frame and the next, then ends.
TEST(KeyChord, BothKeysUpTogether) {
  mono::KeyChord chord;
  step(chord, {true, BOTH, 650});
  EXPECT_TRUE(step(chord, {false, NONE, 700}).isActive()) << "release frame";
  EXPECT_TRUE(step(chord, {false, NONE, 700}).isActive()) << "one frame more for the read order";
  EXPECT_FALSE(step(chord, {false, NONE, 700}).isActive());
}

// One key up first: the SDK reports the other key as Up/Down (or Back/Confirm) later; the chord covers that.
TEST(KeyChord, KeysUpOneAfterTheOther) {
  mono::KeyChord chord;
  step(chord, {true, BOTH, 650});
  EXPECT_TRUE(step(chord, {false, UP, 700}).isActive()) << "first key up";
  for (int frame = 0; frame < 100; ++frame) {
    EXPECT_TRUE(step(chord, {false, UP, 700}).isActive()) << "second key still down, frame " << frame;
  }
  EXPECT_TRUE(step(chord, {false, NONE, 700}).isActive()) << "second key up";
  EXPECT_TRUE(step(chord, {false, NONE, 700}).isActive());
  EXPECT_FALSE(step(chord, {false, NONE, 700}).isActive());
}

// The SDK backdates a PMIC click to the key press when one key is held, so its held time can pass 650 ms.
TEST(KeyChord, ClickWhileOneKeyIsHeldIsAClick) {
  mono::KeyChord chord;
  step(chord, {false, UP, 0});
  EXPECT_FALSE(step(chord, {true, UP, 900}).isActive());
  EXPECT_FALSE(chord.wasPressed());
  EXPECT_FALSE(step(chord, {false, UP, 900}).isActive());
}

// A key that lifts between the SDK's read and ours: the previous frame still counts as both down.
TEST(KeyChord, KeyLiftedBetweenTheTwoReads) {
  mono::KeyChord chord;
  step(chord, {false, BOTH, 0});
  EXPECT_TRUE(step(chord, {true, UP, 650}).wasPressed());
}

// Two frames after both keys were down is too late.
TEST(KeyChord, BothDownTwoFramesAgoIsNotEnough) {
  mono::KeyChord chord;
  step(chord, {false, BOTH, 0});
  step(chord, {false, UP, 0});
  EXPECT_FALSE(step(chord, {true, UP, 700}).isActive());
}

TEST(KeyChord, ClickAfterTheChordIsAClick) {
  mono::KeyChord chord;
  chordAndLetGo(chord);
  EXPECT_FALSE(step(chord, {true, NONE, 0}).isActive());
  EXPECT_FALSE(step(chord, {false, NONE, 10}).isActive());
}

TEST(KeyChord, SecondChordFiresAgain) {
  mono::KeyChord chord;
  chordAndLetGo(chord);
  step(chord, {false, BOTH, 0});
  EXPECT_FALSE(step(chord, {true, BOTH, 300}).wasPressed());
  EXPECT_TRUE(step(chord, {true, BOTH, 660}).wasPressed());
}

}  // namespace
