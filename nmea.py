
def checksum(message: str) -> int:
    return reduce(operator.xor, map(ord, message), 0)


class HCHDT(object):
    def parse(self, message: str) -> None:
        pass

    def create(self, param: dict) -> None:
        data = f""
        cs = checksum(data)
        return f"{self.ID},{data},{checksum}"