#include <ReleaseJsonParser.h>
#include <gtest/gtest.h>

#include <string>

#include "mono/OtaRelease.h"

namespace {

// The size of OtaUpdater.cpp's assetName buffer. ReleaseJsonParser keeps asset names in buffers of the same size.
constexpr size_t ASSET_NAME_SIZE = 48;
constexpr char SUFFIX[] = "-papermono";

// A release as GitHub's API returns it, cut down to the fields the parser reads and a few it skips.
std::string releaseJson(const std::string& tag) {
  const std::string download = "https://github.com/nandanito/crossmono/releases/download/" + tag + "/";
  return R"({"url":"https://api.github.com/repos/nandanito/crossmono/releases/1","tag_name":")" + tag +
         R"(","prerelease":false,"assets":[)"
         R"({"name":"crosspoint-)" +
         tag + R"(-papermono.bin","uploader":{"login":"x"},"size":111,"browser_download_url":")" + download +
         R"(crosspoint.bin"},)"
         R"({"name":"crossmono-)" +
         tag + R"(-papermono-full.bin","uploader":{"login":"x"},"size":222,"browser_download_url":")" + download +
         R"(full.bin"},)"
         R"({"name":"crossmono-)" +
         tag + R"(-papermono.bin","uploader":{"login":"x"},"size":5387152,"browser_download_url":")" + download +
         R"(ota.bin"},)"
         R"({"name":"crossmono-)" +
         tag + R"(-papermono.elf","uploader":{"login":"x"},"size":333,"browser_download_url":")" + download +
         R"(app.elf"}],"tarball_url":null})";
}

}  // namespace

TEST(OtaRelease, DefaultUrlIsTheLatestCrossMonoRelease) {
  EXPECT_STREQ(CROSSMONO_OTA_RELEASE_URL, "https://api.github.com/repos/nandanito/crossmono/releases/latest");
}

TEST(OtaRelease, FormatsTheAssetName) {
  char name[ASSET_NAME_SIZE];
  ASSERT_TRUE(mono::formatAssetName(name, sizeof(name), "0.1.0", SUFFIX));
  EXPECT_STREQ(name, "crossmono-0.1.0-papermono.bin");
  ASSERT_TRUE(mono::formatAssetName(name, sizeof(name), "0.1.0-rc.1", SUFFIX));
  EXPECT_STREQ(name, "crossmono-0.1.0-rc.1-papermono.bin");
}

TEST(OtaRelease, LongestTagThatFitsIs23Characters) {
  const std::string tag = "123.456.789-rc.12345678";
  ASSERT_EQ(tag.size(), 23u);
  char name[ASSET_NAME_SIZE];
  ASSERT_TRUE(mono::formatAssetName(name, sizeof(name), tag.c_str(), SUFFIX));
  EXPECT_EQ(std::string(name), "crossmono-" + tag + "-papermono.bin");
  EXPECT_EQ(std::string(name).size(), ASSET_NAME_SIZE - 1);
}

TEST(OtaRelease, NameThatDoesNotFitIsLeftEmpty) {
  char name[ASSET_NAME_SIZE];
  name[0] = 'x';
  EXPECT_FALSE(mono::formatAssetName(name, sizeof(name), "123.456.789-rc.123456789", SUFFIX));
  EXPECT_STREQ(name, "");
}

TEST(OtaRelease, ZeroSizeBufferIsNotWritten) {
  char name = 'x';
  EXPECT_FALSE(mono::formatAssetName(&name, 0, "0.1.0", SUFFIX));
  EXPECT_EQ(name, 'x');
}

TEST(OtaRelease, ParserFindsTheCrossMonoAppImage) {
  ReleaseJsonParser parser;
  char name[ASSET_NAME_SIZE];
  ASSERT_TRUE(mono::formatAssetName(name, sizeof(name), "0.1.0-rc.1", SUFFIX));
  parser.setFirmwareAssetName(name);
  const std::string json = releaseJson("0.1.0-rc.1");
  parser.feed(json.data(), json.size());

  ASSERT_TRUE(parser.foundTag());
  EXPECT_STREQ(parser.getTagName(), "0.1.0-rc.1");
  ASSERT_TRUE(parser.foundFirmware());
  EXPECT_EQ(parser.getFirmwareSize(), 5387152u);
  EXPECT_STREQ(parser.getFirmwareUrl(), "https://github.com/nandanito/crossmono/releases/download/0.1.0-rc.1/ota.bin");
}

TEST(OtaRelease, ParserMatchesTheLongestName) {
  const std::string tag = "123.456.789-rc.12345678";
  ReleaseJsonParser parser;
  char name[ASSET_NAME_SIZE];
  ASSERT_TRUE(mono::formatAssetName(name, sizeof(name), tag.c_str(), SUFFIX));
  parser.setFirmwareAssetName(name);
  const std::string json = releaseJson(tag);
  parser.feed(json.data(), json.size());

  ASSERT_TRUE(parser.foundFirmware());
  EXPECT_EQ(parser.getFirmwareSize(), 5387152u);
}

TEST(OtaRelease, EmptyNameMatchesNoAsset) {
  ReleaseJsonParser parser;
  char name[ASSET_NAME_SIZE];
  ASSERT_FALSE(mono::formatAssetName(name, sizeof(name), "123.456.789-rc.123456789", SUFFIX));
  parser.setFirmwareAssetName(name);
  const std::string json = releaseJson("0.1.0");
  parser.feed(json.data(), json.size());

  EXPECT_TRUE(parser.foundTag());
  EXPECT_FALSE(parser.foundFirmware());
}
