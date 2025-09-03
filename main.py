from src.infrastructure.logger import setup_logger
from src.infrastructure.container import Container
from loguru import logger


def main():
    setup_logger()
    logger.info("Starting Clip Flow")
    
    container = Container()
    
    container.start_application()


if __name__ == "__main__":
    main()
