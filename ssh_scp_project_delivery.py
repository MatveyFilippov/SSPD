if __name__ == "__main__":
    import sspd
    from sspd import tasks
    try:
        tasks.update_remote_code()
    finally:
        sspd.close_connections()
