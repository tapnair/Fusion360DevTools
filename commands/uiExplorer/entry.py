import adsk.core
import os
import json
from ...lib import fusion360utils as futil
from ... import config
from .ui_tree import get_ui_tree, make_addin_text

app = adsk.core.Application.get()
ui = app.userInterface

CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_ui_explorer'
CMD_NAME = 'User Interface Explorer'
CMD_Description = 'View of all user interface ids'
IS_PROMOTED = True
COMMAND_BESIDE_ID = ''

WORKSPACE_ID = config.design_workspace
TAB_ID = config.design_tab_id
TAB_NAME = config.design_tab_name

PANEL_ID = config.dev_panel_id
PANEL_NAME = config.dev_panel_name
PANEL_AFTER = config.dev_panel_after

PALETTE_NAME = config.ui_palette_name
PALETTE_ID = config.ui_palette_id
PALETTE_URL = './commands/uiExplorer/resources/html/index.html'
PALETTE_DOCKING = adsk.core.PaletteDockingStates.PaletteDockStateRight

ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []


# Executed when add-in is run.
def start():
    # Create a command Definition.
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)
    futil.add_handler(cmd_def.commandCreated, command_created)

    # Create the button command control in the UI
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)
    control.isPromoted = IS_PROMOTED


# Executed when add-in is stopped.
def stop():
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    toolbar_tab = workspace.toolbarTabs.itemById(TAB_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)
    palette = ui.palettes.itemById(PALETTE_ID)

    if command_control:
        command_control.deleteMe()
    if command_definition:
        command_definition.deleteMe()
    if not len(panel.controls):
        panel.deleteMe()
    if not len(toolbar_tab.toolbarPanels):
        toolbar_tab.deleteMe()
    if palette:
        palette.deleteMe()


def command_created(args: adsk.core.CommandCreatedEventArgs):
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)


def command_execute(args: adsk.core.CommandEventArgs):
    palettes = ui.palettes
    palette = palettes.itemById(PALETTE_ID)
    if palette is None:
        palette = palettes.add(
            id=PALETTE_ID,
            name=PALETTE_NAME,
            htmlFileURL=PALETTE_URL,
            isVisible=True,
            showCloseButton=True,
            isResizable=True,
            width=650,
            height=600,
            useNewWebBrowser=True
        )
        futil.add_handler(palette.closed, palette_closed)
        futil.add_handler(palette.navigatingURL, palette_navigating)
        futil.add_handler(palette.incomingFromHTML, palette_incoming)

    if palette.dockingState == adsk.core.PaletteDockingStates.PaletteDockStateFloating:
        palette.dockingState = PALETTE_DOCKING

    palette.isVisible = True


def command_destroy(args: adsk.core.CommandEventArgs):
    global local_handlers
    local_handlers = []


def palette_closed(args: adsk.core.UserInterfaceGeneralEventArgs):
    palette = ui.palettes.itemById(PALETTE_ID)
    if palette:
        palette.deleteMe()


def palette_navigating(args: adsk.core.NavigationEventArgs):
    url = args.navigationURL
    if url.startswith("http"):
        args.launchExternally = True


def palette_incoming(html_args: adsk.core.HTMLEventArgs):
    message_data: dict = json.loads(html_args.data)
    message_action = html_args.action

    if message_action == 'refresh_tree':
        ui_tree = get_ui_tree()
        message_action = 'tree_refresh'
        message_json = json.dumps(ui_tree)

        palette = ui.palettes.itemById(PALETTE_ID)
        palette.sendInfoToHTML(message_action, message_json)

    elif message_action == 'pick_node':
        addin_text = make_addin_text(message_data)
        futil.log(addin_text, force_console=True)
