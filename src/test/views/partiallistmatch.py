class PartialListMatch:
    def __init__(self, length, part, startidx=0, name=None):
        self.length = length
        self.part = part
        self.startidx = startidx
        self.name = name

    def __eq__(self, other):
        assert len(other) == self.length, "{} len missmatch {} != {}".format(
            self.name, len(other), self.length
        )
        assert (
            other[self.startidx: self.startidx + len(self.part)]
            == self.part
        ), "{} partial equality fails {} != {}".format(
            self.name,
            other[self.startidx: self.startidx + len(self.part)],
            self.part,
        )
        return True
