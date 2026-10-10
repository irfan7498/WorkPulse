import workpulse.hooks as hooks


def test_workpulse_app_screen_registration():
    screens = getattr(hooks, "add_to_apps_screen", [])
    assert screens
    assert screens[0]["name"] == "workpulse"
    assert screens[0]["route"] == "/app/workpulse"
