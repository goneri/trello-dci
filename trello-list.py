from trello import TrelloClient

from jinja2 import Environment, FileSystemLoader
import json
from jinja2_markdown import MarkdownExtension
import dateutil
import os

FREE_FIELD_PLUGIN_ID = '56d5e249a98895a9797bebb9'
STORIES = {
    '0eMozAiR-vPPFe5': 'certification',
    '0eMozAiR-cwEIaK': 'usuability',
    '0eMozAiR-ySbOsQ': 'simplify onboarding',
    '0eMozAiR-BPPuN1': 'DCI adoption in Red Hat',
    '0eMozAiR-bJvRos': 'onboarding',
}


client = TrelloClient(
    api_key=os.environ['TRELLO_API_KEY'],
    api_secret=os.environ['TRELLO_API_SECRET'],
    token=os.environ['TRELLO_TOKEN'],
    token_secret=os.environ['TRELLO_SECRET'],
)
ACTIVE_lISTS = {
    'Done': 'done',
    'Pending Review': 'in progress',
    'Doing - (Current Sprint)': 'in progress',
    'Pending (Blocked)': 'to do',
    'To Groom': 'to do',
    'Todo - Backlog': 'to do'}



class Cpt(object):
    def __init__(self):
        self.cur = {'done': 0, 'in progress': 0, 'to do': 0}

    def add(self, status):
        self.cur[status] += 1

    def percent(self):
        s = 0
        for v in self.cur.values():
            s += v
        result = {}
        for i, v in self.cur.items():
            result[i] = int(float(v) * 100 / s)
        return result

def get_stories(client, card):
    plugin_data = client.fetch_json('/cards/' + c.id + '/pluginData')
    fields = []
    for p in plugin_data:
        if p.get('idPlugin') == FREE_FIELD_PLUGIN_ID:
            value = json.loads(p['value'])
            fields = [STORIES[i] for i, v in value['fields'].items() if v]
    return fields

progress_cpt = {}
cards_by_story = {}
dci_board = client.get_board('0eMozAiR')
for l in dci_board.all_lists():
    if l.name in ACTIVE_lISTS.keys():
        trello_list = dci_board.get_list(l.id)
        for c in trello_list.list_cards():
            c.list = l
            c.members = [client.get_member(i) for i in c.member_ids]
            c.status = ACTIVE_lISTS[l.name]
            c.fetch(eager=True)
            c.checklist_items = []
            try:
                c.checklist_items = c._checklists[0].items
            except IndexError:
                pass
            stories = get_stories(client, c)
            if not stories:
                stories += ['other']
            stories += ['all']
            for story in stories:
                if story not in cards_by_story:
                    cards_by_story[story] = []
                    progress_cpt[story] = Cpt()
                cards_by_story[story] += [c]
                progress_cpt[story].add(c.status)

env = Environment(loader=FileSystemLoader('templates'))
env.add_extension(MarkdownExtension)

for story, cards in cards_by_story.items():
    template = env.get_template('story.html.j2')
    with open(story + '.html', 'w') as fd:
        card_by_status = {'done': [], 'in progress': [], 'to do': []}
        for c in cards:
            card_by_status[c.status].append(c)
        fd.write(template.render(
            story=story,
            card_by_status=card_by_status,
            progress=progress_cpt[story].percent()))

template = env.get_template('index.html.j2')
with open('index.html', 'w') as fd:
    fd.write(template.render(
        stories=cards_by_story.keys()))
