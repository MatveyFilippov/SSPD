if __name__ == "__main__":
    import sspd
    try:
        sspd.tasks.update_remote_code()
    finally:
        sspd.close_connections()
