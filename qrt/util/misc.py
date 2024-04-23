from typing import List, Union, Any, Tuple, Generator


def flatten(ll: List[Union[List[Any], Tuple[Any]]]) -> Generator[Any, Any, None]:
    return (i for g in ll for i in g)
