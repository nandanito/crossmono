#include <gtest/gtest.h>

#include <cstdint>

#include "mono/Model.h"
#include "mono/NfcIdentity.h"

namespace {

TEST(NfcIdentity, SplitsTypeAndRevision) {
  EXPECT_EQ(mono::nfcIcType(0x2A), 0x05);
  EXPECT_EQ(mono::nfcIcRevision(0x2A), 0x02);
  EXPECT_EQ(mono::nfcIcType(0xFF), 0x1F);
  EXPECT_EQ(mono::nfcIcRevision(0xFF), 0x07);
}

// Type 5 is 0x28..0x2F; revision 0 (0x28) is not a valid chip.
TEST(NfcIdentity, AcceptsOnlyType5WithRevision) {
  for (int value = 0; value <= 0xFF; ++value) {
    const auto identity = static_cast<uint8_t>(value);
    EXPECT_EQ(mono::isSt25r3916(identity), value >= 0x29 && value <= 0x2F) << "identity 0x" << std::hex << value;
  }
}

// What a floating or absent bus returns.
TEST(NfcIdentity, RejectsIdleBusBytes) {
  EXPECT_FALSE(mono::isSt25r3916(0x00));
  EXPECT_FALSE(mono::isSt25r3916(0xFF));
}

TEST(ResolveModel, AutoUsesTheProbe) {
  const auto full = mono::resolveModel(true, mono::MODEL_OVERRIDE_AUTO);
  EXPECT_EQ(full.model, mono::Model::PaperMono);
  EXPECT_EQ(full.source, mono::ModelSource::Detected);

  const auto lite = mono::resolveModel(false, mono::MODEL_OVERRIDE_AUTO);
  EXPECT_EQ(lite.model, mono::Model::PaperMonoLite);
  EXPECT_EQ(lite.source, mono::ModelSource::Detected);
}

TEST(ResolveModel, OverrideWinsOverTheProbe) {
  for (const bool nfcFound : {false, true}) {
    const auto full = mono::resolveModel(nfcFound, mono::MODEL_OVERRIDE_PAPERMONO);
    EXPECT_EQ(full.model, mono::Model::PaperMono);
    EXPECT_EQ(full.source, mono::ModelSource::Manual);

    const auto lite = mono::resolveModel(nfcFound, mono::MODEL_OVERRIDE_PAPERMONO_LITE);
    EXPECT_EQ(lite.model, mono::Model::PaperMonoLite);
    EXPECT_EQ(lite.source, mono::ModelSource::Manual);
  }
}

// A settings file from a newer build may hold a value this build does not know.
TEST(ResolveModel, UnknownOverrideCountsAsAuto) {
  for (const uint8_t value : {uint8_t{3}, uint8_t{0xFF}}) {
    const auto info = mono::resolveModel(true, value);
    EXPECT_EQ(info.model, mono::Model::PaperMono);
    EXPECT_EQ(info.source, mono::ModelSource::Detected);
  }
}

TEST(ResolveModel, Names) {
  EXPECT_STREQ(mono::modelName(mono::Model::PaperMono), "PaperMono");
  EXPECT_STREQ(mono::modelName(mono::Model::PaperMonoLite), "PaperMono-Lite");
  EXPECT_STREQ(mono::modelSourceName(mono::ModelSource::Detected), "detected");
  EXPECT_STREQ(mono::modelSourceName(mono::ModelSource::Manual), "manual");
}

}  // namespace
