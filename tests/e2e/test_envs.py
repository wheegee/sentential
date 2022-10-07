from tests.helpers import retry

def test_init(invoke):
    init = invoke(["init", "test", "python"])
    assert init.exit_code == 0

def test_write(invoke):
    writes = []
    writes.append(invoke(["envs", "write", "key_1", "one"]))
    writes.append(invoke(["envs", "write", "key_2", "two", "three", "four"]))
    writes.append(invoke(["envs", "write", "key_3", "99"]))
    for write in writes:
        assert write.exit_code == 0

def test_read(invoke):
    read = invoke(["envs", "read"])
    assert read.exit_code == 0
    assert "one" in read.output
    assert "two,three,four" in read.output
    assert "99" in read.output

def test_delete(invoke):
    delete = invoke(["envs", "delete", "key_1"])
    assert delete.exit_code == 0

@retry(5)
def test_read_again(invoke):
    read = invoke(["envs", "read"])
    assert "one" not in read.output
    assert "two,three,four" in read.output
    assert "99" in read.output
    
@retry(5)
def test_clear(invoke):
    result = invoke(["envs", "clear"])
    assert "one" not in result.output
    assert "two,three,four" not in result.output
    assert "99" not in result.output