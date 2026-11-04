#pragma once

#include <cstdint>

// Which PaperMono this is (ADR 0012). One build serves both models: the boot probe looks for the full model's NFC
// chip, and the "Model" setting can override the result.
namespace mono {

enum class Model : uint8_t { PaperMono, PaperMonoLite };
enum class ModelSource : uint8_t { Detected, Manual };

struct ModelInfo {
  Model model;
  ModelSource source;
};

// Values of CrossPointSettings::modelOverride.
constexpr uint8_t MODEL_OVERRIDE_AUTO = 0;
constexpr uint8_t MODEL_OVERRIDE_PAPERMONO = 1;
constexpr uint8_t MODEL_OVERRIDE_PAPERMONO_LITE = 2;

// The override wins; Auto, or any unknown value, uses the probe result.
constexpr ModelInfo resolveModel(const bool nfcFound, const uint8_t overrideValue) {
  switch (overrideValue) {
    case MODEL_OVERRIDE_PAPERMONO:
      return {Model::PaperMono, ModelSource::Manual};
    case MODEL_OVERRIDE_PAPERMONO_LITE:
      return {Model::PaperMonoLite, ModelSource::Manual};
    default:
      return {nfcFound ? Model::PaperMono : Model::PaperMonoLite, ModelSource::Detected};
  }
}

// Product names and About wording: English on every unit, like the rest of About.
constexpr const char* modelName(const Model model) {
  return model == Model::PaperMono ? "PaperMono" : "PaperMono-Lite";
}
constexpr const char* modelSourceName(const ModelSource source) {
  return source == ModelSource::Detected ? "detected" : "manual";
}

// Probes for the NFC chip and holds both radios off. Call once in setup(), after mono::beginInput() has brought up
// the IO expander. Does nothing on other boards.
void probeAtBoot();

// PaperMono builds only. They read the override setting on every call, so a change applies at once.
Model model();
ModelSource source();
const char* name();

}  // namespace mono
