import multiprocessing
import time

def startJarvis():
    print("Process 1 (Jarvis GUI) is running.")
    from main import start
    start()

def listenHotword():
    print("Process 2 (Hotword Detection) is running.")
    from engine.features import hotword
    hotword()

if __name__ == '__main__':
    try:
        p1 = multiprocessing.Process(target=startJarvis)
        p2 = multiprocessing.Process(target=listenHotword)

        p1.start()
        p2.start()

        print("Both processes started...")

        # Continuously monitor processes
        while True:
            if not p1.is_alive():
                print("Jarvis GUI stopped. Terminating Hotword process...")
                if p2.is_alive():
                    p2.terminate()
                break

            if not p2.is_alive():
                print("Hotword Detection stopped unexpectedly!")
                # Optional: Auto-restart hotword detection
                # p2 = multiprocessing.Process(target=listenHotword)
                # p2.start()
                break

            time.sleep(1)

    except KeyboardInterrupt:
        print("Manual interruption received. Terminating processes...")
        if p1.is_alive():
            p1.terminate()
        if p2.is_alive():
            p2.terminate()

    finally:
        if p1.is_alive():
            p1.join()
        if p2.is_alive():
            p2.join()
        print("System stopped.")
