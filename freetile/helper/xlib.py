import Xlib
from Xlib import X, display, protocol

disp = display.Display()
screen = disp.screen()
root = screen.root


def get_current_workspace():
    net_current_desktop = disp.intern_atom('_NET_CURRENT_DESKTOP')
    return root.get_full_property(net_current_desktop, 0).value[0]


def get_active_window():
    return disp.get_input_focus().focus


def getWmState(win):
    net_wm_state = disp.intern_atom('_NET_WM_STATE')
    prop = win.get_full_property(net_wm_state, X.AnyPropertyType)
    if prop is None:
        return []
    else:
        return prop.value


def getWmWindowType(win):
    net_wm_window_type = disp.intern_atom('_NET_WM_WINDOW_TYPE')
    prop = win.get_full_property(net_wm_window_type, X.AnyPropertyType)
    if prop is None:
        return []
    else:
        return prop.value


def edit_prop(window, mode, name, value):
    cm_event = protocol.event.ClientMessage(window=window, client_type=disp.intern_atom(name), data=(32, [mode, disp.intern_atom(value), 0, 0, 0]))
    disp.send_event(root, cm_event, (X.SubstructureRedirectMask | X.SubstructureNotifyMask))


def get_root_window_property(name):
    return root.get_property(disp.intern_atom(name), Xlib.Xatom.CARDINAL, 0, 32).value


def get_frame_extents(win):
    frame_extents = win.get_property(disp.intern_atom("_NET_FRAME_EXTENTS"), Xlib.Xatom.CARDINAL, 0, 32)
    if frame_extents is None:
        return 0, 0, 0, 0
    else:
        return frame_extents.value


def get_wm_opaque_region(win):
    net_wm_opaque_region = disp.intern_atom('_NET_WM_OPAQUE_REGION')
    prop = win.get_full_property(net_wm_opaque_region, X.AnyPropertyType)
    if prop is None:
        result=[]
    else:
        result=list(prop.value)
    result+=[0]*(8-len(result))
    return result


def get_wm_class_and_state(win):
    wm_class = win.get_wm_class()
    wm_state = win.get_wm_state()
    minimized = not wm_state.state == 1
    return wm_class, minimized
