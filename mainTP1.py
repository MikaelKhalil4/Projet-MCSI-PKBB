from osc_server import OSCServer
from time import sleep

def main():
    user_input = input("Is collaboration mode enabled? Enter 1 for Yes or 0 for No: ")
    
    # Validate and convert input to a boolean
    if user_input == "1":
        is_collab = True
    elif user_input == "0":
        is_collab = False
    else:
        print("Invalid input! Please enter 1 or 0.")
        exit(1)  # Exit the program if the input is invalid

        
    osc_server = OSCServer(is_collab)
    #here should start all everything like face tracking etc


    try:
        sleep(1000)
    except KeyboardInterrupt:
        pass
    finally:
        osc_server.stop()

if __name__ == "__main__":
    main()
