#include <gtest/gtest.h>

#include "mono/CuePolicy.h"

namespace {

using mono::Leds;

TEST(LowBattery, StartsHigh) {
  mono::LowBattery battery;
  EXPECT_FALSE(battery.low());
  EXPECT_FALSE(battery.takeAlert());
}

TEST(LowBattery, ThresholdAndHysteresis) {
  mono::LowBattery battery;
  battery.update(11, false);
  EXPECT_FALSE(battery.low());
  battery.update(10, false);
  EXPECT_TRUE(battery.low());
  battery.update(12, false);
  EXPECT_TRUE(battery.low()) << "stays low below the clear level";
  battery.update(13, false);
  EXPECT_FALSE(battery.low());
}

TEST(LowBattery, UsbClearsTheCue) {
  mono::LowBattery battery;
  battery.update(5, false);
  ASSERT_TRUE(battery.low());
  battery.update(5, true);
  EXPECT_FALSE(battery.low());
  battery.update(5, false);
  EXPECT_TRUE(battery.low());
}

// An alert held back while Sound is Off must not play once USB is in or the battery is fine again.
TEST(LowBattery, PendingAlertEndsWhenTheBatteryIsFine) {
  mono::LowBattery usb;
  usb.update(8, false);
  usb.update(8, true);
  EXPECT_FALSE(usb.takeAlert());

  mono::LowBattery recovered;
  recovered.update(8, false);
  recovered.update(20, false);
  EXPECT_FALSE(recovered.takeAlert());
}

TEST(LowBattery, NotLowOnUsb) {
  mono::LowBattery battery;
  battery.update(3, true);
  EXPECT_FALSE(battery.low());
  EXPECT_FALSE(battery.takeAlert());
}

TEST(LowBattery, AlertOncePerBoot) {
  mono::LowBattery battery;
  battery.update(9, false);
  EXPECT_TRUE(battery.takeAlert());
  EXPECT_FALSE(battery.takeAlert());
  battery.update(50, false);
  battery.update(9, false);
  EXPECT_TRUE(battery.low());
  EXPECT_FALSE(battery.takeAlert()) << "low again, but the alert already played";
}

TEST(Leds, OffWhenDisabled) { EXPECT_EQ(mono::ledsFor(false, true, true, true), Leds{}); }

TEST(Leds, OneLegPerCue) {
  EXPECT_EQ(mono::ledsFor(true, false, false, false), Leds{});
  EXPECT_EQ(mono::ledsFor(true, true, false, false), (Leds{true, false, false}));
  EXPECT_EQ(mono::ledsFor(true, false, true, false), (Leds{false, true, false}));
  EXPECT_EQ(mono::ledsFor(true, false, false, true), (Leds{false, false, true}));
  EXPECT_EQ(mono::ledsFor(true, false, true, true), (Leds{false, true, true}));
}

constexpr unsigned long PERIOD = mono::LOW_BATTERY_BLINK_PERIOD_MS;
constexpr unsigned long ON = mono::LOW_BATTERY_BLINK_ON_MS;

TEST(Blink, OffWhileInactive) {
  mono::Blink blink;
  EXPECT_FALSE(blink.update(false, 0));
  EXPECT_FALSE(blink.update(false, PERIOD));
}

TEST(Blink, FlashesOncePerPeriod) {
  mono::Blink blink;
  const unsigned long start = 5000;
  ASSERT_TRUE(blink.update(true, start)) << "the first flash comes at once";
  blink.shown(true, start);
  EXPECT_TRUE(blink.update(true, start + ON - 1));
  EXPECT_FALSE(blink.update(true, start + ON));
  blink.shown(false, start + ON);
  EXPECT_FALSE(blink.update(true, start + PERIOD - 1));
  EXPECT_TRUE(blink.update(true, start + PERIOD));
}

// The render task can hold the LED write back; the flash is late, not lost, and lasts its full time.
TEST(Blink, ALateWriteDelaysTheFlash) {
  mono::Blink blink;
  EXPECT_TRUE(blink.update(true, 0));
  EXPECT_TRUE(blink.update(true, 900)) << "still due: the write has not happened";
  blink.shown(true, 900);
  EXPECT_TRUE(blink.update(true, 900 + ON - 1));
  EXPECT_FALSE(blink.update(true, 900 + ON));
  blink.shown(false, 900 + ON);
  EXPECT_FALSE(blink.update(true, 900 + PERIOD - 1));
  EXPECT_TRUE(blink.update(true, 900 + PERIOD));
}

// A stall longer than a period: the next flash waits until the LED has shown the end of this one, so red cannot
// stay lit with nothing left to write.
TEST(Blink, StallLongerThanAPeriod) {
  mono::Blink blink;
  blink.update(true, 0);
  blink.shown(true, 0);
  EXPECT_FALSE(blink.update(true, 2 * PERIOD)) << "first ask for red off";
  EXPECT_FALSE(blink.update(true, 2 * PERIOD + 10)) << "still off until the write";
  blink.shown(false, 2 * PERIOD + 10);
  EXPECT_TRUE(blink.update(true, 2 * PERIOD + 20)) << "then the overdue flash";
}

// The off write failed while the cue was inactive, and the cue came back with red still lit: the lit leg counts as
// the flash and goes off after its time, instead of staying on.
TEST(Blink, ReactivatedWhileRedIsStillLit) {
  mono::Blink blink;
  blink.update(true, 0);
  blink.shown(true, 0);
  EXPECT_FALSE(blink.update(false, 50));
  blink.shown(true, 50);  // the off write missed the lock
  EXPECT_TRUE(blink.update(true, 60));
  blink.shown(true, 60);
  EXPECT_FALSE(blink.update(true, 50 + ON)) << "goes off instead of staying lit";
}

// A write that did not light the red leg does not count as the flash.
TEST(Blink, OnlyARedWriteCounts) {
  mono::Blink blink;
  blink.update(true, 0);
  blink.shown(false, 0);
  EXPECT_TRUE(blink.update(true, 2 * ON)) << "still due";
}

TEST(Blink, InactiveResets) {
  mono::Blink blink;
  blink.update(true, 0);
  blink.shown(true, 0);
  blink.update(true, ON);
  EXPECT_FALSE(blink.update(false, 1000));
  EXPECT_TRUE(blink.update(true, 1001)) << "low again: flash at once";
}

TEST(TonePlayer, SilentUntilPlayed) {
  mono::TonePlayer player;
  EXPECT_FALSE(player.playing());
  EXPECT_EQ(player.update(1000), 0);
}

TEST(TonePlayer, PlaysTheSequenceThenStops) {
  mono::TonePlayer player;
  player.play(mono::LOW_BATTERY_ALERT, 1000);
  EXPECT_TRUE(player.playing());
  EXPECT_EQ(player.update(1000), 2000);
  EXPECT_EQ(player.update(1079), 2000);
  EXPECT_EQ(player.update(1080), 0) << "the gap";
  EXPECT_EQ(player.update(1179), 0);
  EXPECT_EQ(player.update(1180), 2000) << "second beep";
  EXPECT_EQ(player.update(1259), 2000);
  EXPECT_EQ(player.update(1260), 0);
  EXPECT_FALSE(player.playing());
}

// A slow loop pass skips the parts it missed instead of replaying them.
TEST(TonePlayer, CatchesUpAfterASlowPass) {
  mono::TonePlayer player;
  player.play(mono::LOW_BATTERY_ALERT, 0);
  EXPECT_EQ(player.update(200), 2000) << "inside the second beep";
  EXPECT_EQ(player.update(5000), 0);
  EXPECT_FALSE(player.playing());
}

TEST(TonePlayer, KeyClick) {
  mono::TonePlayer player;
  player.play(mono::KEY_CLICK, 10);
  EXPECT_EQ(player.update(10), 3000);
  EXPECT_EQ(player.update(25), 0);
}

// Each tone or gap is a new segment, even with the same frequency as the one before.
TEST(TonePlayer, SegmentChangesOncePerToneOrGap) {
  mono::TonePlayer player;
  const unsigned idle = player.segment();
  player.play(mono::LOW_BATTERY_ALERT, 0);
  const unsigned beep1 = player.segment();
  EXPECT_NE(beep1, idle);
  player.update(10);
  EXPECT_EQ(player.segment(), beep1) << "same tone";
  player.update(200);
  EXPECT_EQ(player.segment(), beep1 + 2) << "past the gap, in the second beep";
  player.stop();
  EXPECT_EQ(player.segment(), beep1 + 3);
}

// Stopping an idle player changes nothing, so Sound = Off does not touch the buzzer on every pass.
TEST(TonePlayer, StopWhenIdleKeepsTheSegment) {
  mono::TonePlayer player;
  const unsigned idle = player.segment();
  player.stop();
  player.stop();
  EXPECT_EQ(player.segment(), idle);
  player.play(mono::KEY_CLICK, 0);
  player.update(100);
  const unsigned done = player.segment();
  player.stop();
  EXPECT_EQ(player.segment(), done) << "already finished";
}

// The tone timer is armed with what is left of the current tone.
TEST(TonePlayer, RemainingTime) {
  mono::TonePlayer player;
  EXPECT_EQ(player.remainingMs(0), 0UL);
  player.play(mono::LOW_BATTERY_ALERT, 1000);
  player.update(1000);
  EXPECT_EQ(player.remainingMs(1000), 80UL);
  player.update(1030);
  EXPECT_EQ(player.remainingMs(1030), 50UL);
  player.update(1100);
  EXPECT_EQ(player.remainingMs(1100), 80UL) << "the gap: 100 ms from 1080";
  player.update(5000);
  EXPECT_EQ(player.remainingMs(5000), 0UL);
}

TEST(TonePlayer, StopSilences) {
  mono::TonePlayer player;
  player.play(mono::LOW_BATTERY_ALERT, 0);
  player.stop();
  EXPECT_FALSE(player.playing());
  EXPECT_EQ(player.update(10), 0);
}

}  // namespace
