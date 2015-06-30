CPU_IDLE_THRESHOLD = 0.05


def always_idle(config):
    return True


def always_active(config):
    return False


def cpu_idle(sample):
    if sample.kind == 'cpu_util':
        return sample.value < CPU_IDLE_THRESHOLD
