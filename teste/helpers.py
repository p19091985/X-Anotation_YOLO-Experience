class DummyVar:

    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class DummyLabel:

    def __init__(self):
        self.text = None

    def config(self, **kwargs):
        if 'text' in kwargs:
            self.text = kwargs['text']


class DummyEntry:

    def __init__(self, value=''):
        self.value = value
        self.focused = False

    def get(self):
        return self.value

    def focus(self):
        self.focused = True


class DummyFrame:

    def __init__(self):
        self.pack_calls = []
        self.forgotten = False

    def pack(self, **kwargs):
        self.pack_calls.append(kwargs)
        self.forgotten = False

    def pack_forget(self):
        self.forgotten = True


class FakeTree:

    def __init__(self):
        self.rows = {}
        self.current_selection = ()
        self.focused = None

    def get_children(self):
        return list(self.rows.keys())

    def delete(self, item):
        self.rows.pop(str(item), None)

    def insert(self, parent, index, iid=None, values=()):
        row_id = str(len(self.rows)) if iid is None else str(iid)
        self.rows[row_id] = tuple(values)
        return row_id

    def selection(self):
        return self.current_selection

    def selection_set(self, iid):
        self.current_selection = (str(iid),)

    def focus(self, iid=None):
        if iid is not None:
            self.focused = str(iid)
        return self.focused

    def item(self, iid, option=None):
        values = self.rows[str(iid)]
        if option == 'values':
            return values
        return {'values': values}
