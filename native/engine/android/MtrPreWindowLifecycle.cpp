#include "application/ApplicationManager.h"
#include "base/Log.h"
#include "engine/EngineEvents.h"
#include "platform/BasePlatform.h"

namespace {

// Cocos' normal close handler exists only after cocos_main creates the app.
// Register at library load, before GameActivity can destroy its first Surface.
class PreWindowCloseGuard final {
public:
    PreWindowCloseGuard() {
        _listener.bind([](const cc::WindowEvent &event) {
            if (event.type != cc::WindowEvent::Type::CLOSE) return;
            if (CC_CURRENT_APPLICATION()) return;
            // This callback and AndroidPlatform::loop run on the same app thread.
            cc::BasePlatform::getPlatform()->exit();
#if CC_DEBUG
            CC_LOG_DEBUG("MTR_NATIVE_PRE_WINDOW_CLOSE_EXIT_REQUESTED");
#endif
        });
    }

private:
    cc::events::WindowEvent::Listener _listener;
};

PreWindowCloseGuard preWindowCloseGuard;

} // namespace
