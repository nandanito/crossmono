#include <gtest/gtest.h>

#include "mono/PowerRelease.h"

namespace {

constexpr bool MAIN_LOOP = false;  // MappedInputManager::update()
constexpr bool TRANSFER = true;    // MappedInputManager::update(true)

// Feeds one input update and returns whether the release is reported after it.
bool step(mono::PowerRelease& release, const bool deferred, const bool released = false) {
  release.update(deferred, released);
  return release.wasReleased();
}

TEST(PowerRelease, StartsClear) {
  const mono::PowerRelease release;
  EXPECT_FALSE(release.wasReleased());
  EXPECT_FALSE(mono::powerRelease().wasReleased());
}

TEST(PowerRelease, MainLoopReleaseIsNotRepeated) {
  // The main loop reads its own release from the buttons; nothing is kept for later.
  mono::PowerRelease release;
  EXPECT_FALSE(step(release, MAIN_LOOP, true));
  EXPECT_FALSE(step(release, MAIN_LOOP));
}

TEST(PowerRelease, TransferReleaseReachesTheNextMainLoopUpdateOnce) {
  mono::PowerRelease release;
  EXPECT_FALSE(step(release, TRANSFER, true));
  EXPECT_FALSE(step(release, TRANSFER));
  EXPECT_FALSE(step(release, TRANSFER));
  EXPECT_TRUE(step(release, MAIN_LOOP));
  EXPECT_FALSE(step(release, MAIN_LOOP));
}

TEST(PowerRelease, ReportLastsUntilTheNextUpdate) {
  // The blocking loop that runs after the main loop's checks does not see the report again.
  mono::PowerRelease release;
  step(release, TRANSFER, true);
  EXPECT_TRUE(step(release, MAIN_LOOP));
  EXPECT_FALSE(step(release, TRANSFER));
  EXPECT_FALSE(step(release, MAIN_LOOP));
}

TEST(PowerRelease, SeveralReleasesInOneTransferAreOneReport) {
  mono::PowerRelease release;
  step(release, TRANSFER, true);
  step(release, TRANSFER);
  step(release, TRANSFER, true);
  EXPECT_TRUE(step(release, MAIN_LOOP));
  EXPECT_FALSE(step(release, MAIN_LOOP));
}

TEST(PowerRelease, EachTransferPassKeepsItsOwnRelease) {
  mono::PowerRelease release;
  step(release, TRANSFER, true);
  EXPECT_TRUE(step(release, MAIN_LOOP));
  step(release, TRANSFER, true);
  EXPECT_TRUE(step(release, MAIN_LOOP));
}

TEST(PowerRelease, ScreenChangeDropsAKeptRelease) {
  mono::PowerRelease release;
  step(release, TRANSFER, true);
  release.forget();
  EXPECT_FALSE(step(release, MAIN_LOOP));
}

TEST(PowerRelease, ForgetLeavesTheCurrentReport) {
  // Like a release read from the buttons, a report stays visible for the rest of its update.
  mono::PowerRelease release;
  step(release, TRANSFER, true);
  EXPECT_TRUE(step(release, MAIN_LOOP));
  release.forget();
  EXPECT_TRUE(release.wasReleased());
  EXPECT_FALSE(step(release, MAIN_LOOP));
}

}  // namespace
