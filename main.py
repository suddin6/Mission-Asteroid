'''
Names: Grace Jowett and Sumaya Uddin
Professor: Solmaz Salehian
Course: CSI 1320
Due Date: April 16, 2025
Project I
Summary: An interactive asteroid game.
'''

#import built-in modules
import asyncio
from asyncio import events
import pygame
from os.path import join
import os
from random import randint, choice

#initialize pygame
pygame.init()

#the size of the screen and caption
screen = pygame.display.set_mode((800,600))
pygame.display.set_caption('MISSION ASTEROID')

#empty lists for elements in the background
star_bg = []
asteroid_bg = []
bonus_bg = []
fake_bg = []
laser_bg = []
clock_bg = []

#cooldown for lasers
start_time = pygame.time.get_ticks()
cooldown = 250

#sound effects
laser_sound = pygame.mixer.Sound('sounds/laser.ogg')
explosion_sound = pygame.mixer.Sound('sounds/explosion.ogg')
fake_asteroid_sound = pygame.mixer.Sound('sounds/asteroid.ogg')
clock_sound = pygame.mixer.Sound('sounds/clock.ogg')

#countdown starts at 2 minutes
countdown_time = 120

#starting score of 0
current_score = 0
final_score = 0

#flashing effect
flashing = False

#variables to keep track of game pause
pauseFlashing = False
paused = False
paused_timeTotal = 0
pausedStart = None

#saved score for appending to file
savedScore = False

#storing when the game starts
game_start = None

#the main function setup
async def main():

    '''
    The main function is where the general code is located.

    This function mainly calls the other functions of the code
    and allows the user to exit the game.
    '''

    #access the variables from outside the functions
    global countdown_time, flashing, current_score, pauseFlashing, paused, pauseFlashing, freeze, paused_timeTotal, pausedStart, game_start
    
    #time of the last laser shot
    shoot_time = 0

    #regulates the speed of the game
    clock = pygame.time.Clock()

    #the time the game starts
    game_start = pygame.time.get_ticks()

    #variable to track when game is unpaused
    unpaused = False
    
    #different font sizes
    try:
        #use specified font
        font = pygame.font.Font("fonts/SpaceMono-Bold.ttf", 43)
        font2 = pygame.font.Font("fonts/SpaceMono-Regular.ttf", 30) 
        font3 = pygame.font.Font("fonts/SpaceMono-Bold.ttf", 50)
    except:
        #if not found, use default
        font = pygame.font.Font(None, 43)
        font2 = pygame.font.Font(None, 30) 
        font3 = pygame.font.Font(None, 50)

    #call the other functions
    spaceship, spaceshipRect = spaceship_draw()
    star_img = star()
    asteroid1_img, asteroid2_img = asteroid()
    bonus_img = bonus_asteroid()
    fake_img = fake_asteroid()
    laser_img = laser_draw()
    clock_img = extra_time()
    
    #running of the game
    running = True
    remaining_time = 120
    current_score = 0
    started = False

    while running:
        #display the start screen before user clicks play
        if not started:
            #if user presses button, start the clock
            if await start_screen():
                started = True
                game_start = pygame.time.get_ticks()
                remaining_time = 120

        else:
            #limits the game to 60 frames per second; dt for delta time in seconds
            dt = clock.tick(60)/1000
            dt = min(dt, 0.05)

            events = pygame.event.get()
            for event in events:
                #allows user to exit the game
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    #press p to pause the game
                    if event.key == pygame.K_p:
                        await pause()
                        break

                    #press r to resume the game AFTER user presses pause
                    if event.key == pygame.K_r and paused:
                        await resume()
                        break

                    #press left shift to restart the game AFTER user presses pause
                    if event.key == pygame.K_LSHIFT and paused:
                        restart()

                    #press right shift to replay the game AFTER timer hits 0
                    if event.key == pygame.K_RSHIFT and remaining_time <= 0:
                        flashReset()
                        reset_game()

            #if the game is paused, flash and freeze the screen
            if paused:
                if flashing:
                    flashing = False
                    flashReset()
                    continue
                else:
                    if freeze:
                        screen.blit(freeze, (0,0))

                    #keep track of how long the game is paused
                    if pausedStart is None:
                        pausedStart = pygame.time.get_ticks()

                    #overlay of the paused screen
                    pauseFade = pygame.Surface((800, 600))
                    pauseFade.fill('black')
                    pauseFade.set_alpha(120)
                    screen.blit(pauseFade, (0,0))

                    #paused message
                    pausedFont = pygame.font.Font("fonts/SpaceMono-Bold.ttf", 50)

                    shadow = pausedFont.render('PAUSED!', True, (30, 120, 60))
                    screen.blit(shadow, (302, 202))
                    
                    pausedText = pausedFont.render('PAUSED!', True, (80, 255, 120))
                    screen.blit(pausedText, (300, 200))

                    #calling the resume_button and restart_button functions to display on pause screen
                    await resume_button(events)
                    await restart_button(events)

                    #update the screen and continue with the game
                    pygame.display.update()
                    await asyncio.sleep(0)
                    continue

            #play the game as usual when not paused
            screen.fill('black')

            #call all the functions
            background(star_img, dt)

            move_asteroid(asteroid1_img, asteroid2_img, dt)
            move_bonus(bonus_img, dt)
            move_fake(fake_img, dt)
            move_clock(clock_img, dt)

            spaceship_move(spaceship, spaceshipRect, dt)
            shoot_time = laser_shoot(spaceshipRect, shoot_time, cooldown, laser_img)
            laser_update(dt, laser_img)

            #when unpaused, calculate the remaining time from paused time so user can start from where they left off
            if not paused:
                timeElapsed = (pygame.time.get_ticks() - game_start - paused_timeTotal)
                remaining_time = max(0, countdown_time - timeElapsed//1000)

            #stop updating the score after the time is 0
            if remaining_time > 0:
                collision(spaceshipRect, laser_bg, font)
                score(font2)
            else:
                final_score = current_score

            #drawing the timer on the screen
            draw_timer(font,remaining_time)

            #once game is over, flash and update the screen
            if game_over(remaining_time, font3, events):
                flashing = True
                pygame.display.update()
                continue

            #call the pause_button function
            pause_button(remaining_time, events)

            #flash the screen before and after pausing
            if pauseFlashing:
                flash2_time = pygame.time.get_ticks()
                while pygame.time.get_ticks() - flash2_time < 300:
                   screen.fill((250,249,246))
                   pygame.display.update()
                   await asyncio.sleep(0)
                   continue
                else:
                    pauseFlashing = False

            #updates the screen
            pygame.display.update()
            await asyncio.sleep(0)
        
    #quit the game
    pygame.quit()

#the star function
def star():

    '''
    This function draws the stars in the background.
    '''

    #load the stars, otherwise explain the error and tell user to wait
    try:
        star_img = pygame.image.load(join('images', 'Star.png')).convert_alpha()
        
    except pygame.error:
        print("there was an error loading the stars. please try again later")
        return

    #randomly draw 200 stars
    for i in range(200):
        starX = randint(0,800)
        starY = randint(0,800)

        star_bg.append([starX, starY]) #add the stars to the list 

    #return the star image
    return star_img

#the background function
def background(star_img, dt):

    '''
    In this function, the stars are drawn in the background.

    They are also constantly moving to the right and twinkling,
    giving the user a space vibe.
    '''
    
    global star_bg #calls the star_bg from outside the functions
 
    starSpeed = 0.1 * 1000 * dt #sets the speed of the stars using the delta time

    #scaling the stars and make them twinkle
    starSize = randint(1,10)
    background = pygame.transform.scale(star_img, (starSize, starSize))

    #loop through each star and move it to the right
    for star in star_bg:
        star[0] += starSpeed

        #once the star passes the width of the game, give the star a random position
        if star[0] > 800:
            star[0] = 0 #reset the x coordinate to 0
            star[1] = randint(0,600) #reset the y coordinate to a random int

        starTuple = (star[0], star[1]) #tuple of the star positions
        screen.blit(background, starTuple) #shows the stars in the background of the game


#the asteroid function
def asteroid():
    
    '''
    This function draws two different types of asteroids
    in the background for the player to shoot.
    '''

    #load the asteroids, otherwise explain the error and tell user to wait
    try:
        asteroid1 = pygame.image.load(join('images', 'Asteroid_1.png')).convert_alpha()
        asteroid2 = pygame.image.load(join('images', 'Asteroid_2.png')).convert_alpha()

    except pygame.error:
        print("there was an error loading the asteroids. please try again later")
        return None, None

    #randomly draw 6 asteroids
    for i in range(6):
        #x and y coordinates for asteroid 1
        asteroid1_x = randint(0,800)
        asteroid1_y = randint(0,800)

        #x and y coordinates for asteroid 2
        asteroid2_x = randint(0,800)
        asteroid2_y = randint(0,800)

        #append the x and y coordinates along with asteroid type using a dictionary
        asteroid_bg.append({"x": asteroid1_x, "y": asteroid1_y, "img": "asteroid1"})
        asteroid_bg.append({"x": asteroid2_x, "y": asteroid2_y, "img": "asteroid2"})

    #return the asteroid images
    return asteroid1, asteroid2

#the move_asteroid function
def move_asteroid(asteroid1_img, asteroid2_img, dt):

    '''
    This function allows both types of asteroids to
    continuously fall down the screen.
    '''
    
    global asteroid_bg, final_score #call the asteroid_bg and final_score variable from outside the functions

    asteroidSpeed = [0.35, 0.3, 0.2, 0.25, 0.4] #various speeds for the asteroids

    #scaling both asteroids
    asteroid1Size = 55
    a1 = pygame.transform.scale(asteroid1_img, (asteroid1Size, asteroid1Size))
    asteroid2Size = 55
    a2 = pygame.transform.scale(asteroid2_img, (asteroid2Size, asteroid2Size))

    #loop through each asteroid in the list
    for i in range(len(asteroid_bg)):
        ast = asteroid_bg[i]
        
        #assign the keys of the dict in the list to variables
        x = ast['x']
        y = ast['y']
        asteroidType = ast['img']

        #restart the speed at index 0 once it goes beyond the list of speeds
        speed = asteroidSpeed[i % len(asteroidSpeed)]

        y += speed * 1000 * dt #moves the asteroids down the screen at random speeds using delta time
        
        if final_score > 50:
            x += randint(-2,2)

        if final_score > 150:
            x += randint(-4,4)

        if final_score > 300:
            y += speed * 1050 * dt

        #if the asteroids go off the screen, give them new values to start from the top
        if y > 800:
            y = 0
            x = randint(0, 800)

        #make the keys of the list equal the new x and y values
        ast['x'] = x
        ast['y'] = y

        #look at image type and make it equal the scaled asteroid image
        if asteroidType == 'asteroid1':
            asteroid_imgs = a1
        else:
            asteroid_imgs = a2

        #show the asteroids on the screen
        asteroidTuple = (x, y)
        screen.blit(asteroid_imgs, asteroidTuple)

#the bonus asteroid function
def bonus_asteroid():
    '''
    This function draws a bonus asteroid in the
    background for the player to shoot.
    '''

    #load the bonus asteroid, otherwise explain the error and tell user to wait
    try:
        bonus = pygame.image.load(join('images', 'Bonus_Asteroid.png')).convert_alpha()

    except pygame.error:
        print("there was an error loading the bonus asteroid. please try again later")
        return None

    #randomly draw 1 bonus asteroid
    for i in range(1):
        #x and y coordinates for bonus asteroid
        bonusX = randint(0,800)
        bonusY = randint(0,800)

        #append the x and y coordinates in the bonus asteroid list
        bonus_bg.append([bonusX, bonusY])

    #return the bonus asteroid image
    return bonus

#the move_bonus function
def move_bonus(bonus_img, dt):
    
    '''
    This function allows 1 bonus asteroid to
    continuously fall down the screen.
    '''
    
    global bonus_bg, final_score #call the bonus_bg and final_score variable from outside the functions

    bonusSpeed = [0.5, 0.2, 0.3, 0.4] #various speeds for the bonus asteroids

    #loop through each bonus asteroid in the list
    for ast in bonus_bg:
        
        #choose a random speed from a list
        speed = choice(bonusSpeed)

        ast[1] += speed * 1000 * dt #moves the asteroids down the screen at random speeds using delta time

        if final_score > 50:
            ast[0] += randint(-2,2)

        if final_score > 150:
            ast[0] += randint(-4,4)

        if final_score > 300:
            ast[1] += speed * 1050 * dt
            
        #if the asteroids go off the screen, give them new values to start from the top
        if ast[1] > 800:
            ast[1] = 0
            ast[0] = randint(0, 800)

        #show the asteroids on the screen
        bonusTuple = (ast[0], ast[1])
        screen.blit(bonus_img, bonusTuple)

#the fake asteroid function
def fake_asteroid():
    
    '''
    This function draws a fake asteroid in the
    background for the player to shoot.
    '''

    #load the fake asteroid, otherwise explain the error and tell user to wait
    try:
        fake = pygame.image.load(join('images', 'Fake_Asteroid.png')).convert_alpha()

    except pygame.error:
        print("there was an error loading the fake asteroid. please try again later")
        return None

    #randomly draw 5 asteroids
    for i in range(5):
        #x and y coordinates for the fake asteroid
        fakeX = randint(0,800)
        fakeY = randint(0,800)

        #append the x and y coordinates of the fake asteroid to the list
        fake_bg.append([fakeX, fakeY])

    #return the fake asteroid image
    return fake

#the move_fake function
def move_fake(fake_img, dt):
    
    '''
    This function allows 4 fake asteroids to
    continuously fall down the screen.
    '''
    
    global fake_bg, final_score #call the fake_bg variable from outside the functions

    fakeSpeed = [0.3, 0.2, 0.25, 0.4] #various speeds for the fake asteroids

    #scaling the asteroid
    fakeSize = 55
    f = pygame.transform.scale(fake_img, (fakeSize, fakeSize))

    #loop through each asteroid in the list
    for ast in fake_bg:
        
        #choose a random speed from the list
        speed = choice(fakeSpeed)

        ast[1] += speed * 1000 * dt #moves the asteroids down the screen at random speeds with delta time

        if final_score > 50:
            ast[0] += randint(-2,2)

        if final_score > 150:
            ast[0] += randint(-4,4)

        if final_score > 300:
            ast[1] += speed * 1050 * dt
            
        #if the asteroids go off the screen, give them new values to start from the top
        if ast[1] > 800:
            ast[1] = 0
            ast[0] = randint(0, 800)

        #show the asteroids on the screen
        fakeTuple = (ast[0], ast[1])
        screen.blit(f, fakeTuple)

#the extra time function
def extra_time():
    
    '''
    This function draws a green clock in the
    background for the player to shoot and gain
    extra time.
    '''

    #load the clock, otherwise explain the error and tell user to wait
    try:
        clock = pygame.image.load(join('images', 'Extra_Time.png')).convert_alpha()

    except pygame.error:
        print("there was an error loading the clock. please try again later")
        return None

    #randomly draw 1 clock
    for i in range(1):
        #x and y coordinates for the clock
        clockX = randint(0,800)
        clockY = randint(0,800)

        #append the x and y coordinates of the clock to the list
        clock_bg.append([clockX, clockY])

    #return the clock image
    return clock

#the move_clock function
def move_clock(clock_img, dt):
    
    '''
    This function allows 1 clock to
    continuously fall down the screen.
    '''
    
    global clock_bg, final_score #access the clock_bg and final_score variable from outside the functions

    clockSpeed = [0.3, 0.2, 0.25, 0.4] #various speeds for the clocks

    #scaling the clock
    clockSize = 55
    c = pygame.transform.scale(clock_img, (clockSize, clockSize))

    #loop through each clock in the list
    for clock in clock_bg:
        
        #choose a random speed from the list
        speed = choice(clockSpeed)

        clock[1] += speed * 1000 * dt #moves the clocks down the screen at random speeds with delta time

        if final_score > 50:
            clock[0] += randint(-2,2)

        if final_score > 150:
            clock[0] += randint(-4,4)

        if final_score > 300:
            clock[1] += speed * 1050 * dt
            
        #if the clocks go off the screen, give them new values to start from the top
        if clock[1] > 800:
            clock[1] = 0
            clock[0] = randint(0, 800)

        #show the clocks on the screen
        clockTuple = (clock[0], clock[1])
        screen.blit(c, clockTuple)

#the spaceship_draw function
def spaceship_draw():

    '''
    This function draws the spaceship.

    The spaceship is essentially the play.
    '''

    #load the spaceship, otherwise display error and return a random rect
    try:
        ship = pygame.image.load(join('images', 'Space_Ship.png')).convert_alpha()
    except:
        print("there was some trouble loading the ship. please try again later.")
        return pygame.Rect(0, 400, 50, 50)
    
    #scales the image
    spaceshipSize = 40
    spaceship = pygame.transform.scale(ship, (spaceshipSize, spaceshipSize))

    spaceshipRect = spaceship.get_rect() #turn img into a rect

    #position the rectangle
    spaceshipRect.x = 0
    spaceshipRect.y = screen.get_height() - spaceshipRect.height

    #returns the rectangle version of the ship to be used in move function
    return spaceship, spaceshipRect

#the spaceship move function
def spaceship_move(spaceship, spaceshipRect, dt):

    '''
    This function allows the player to move the ship in any way
    they desire using the WASD controls.

    There is also a boundary that prevents the user from moving the
    ship too high in the game.
    '''
    
    #speed at which the spaceship moves with delta time
    speed = 0.7 * 1000 * dt

    #height and width of screen
    height = 600
    width = 800

    limit = height - 200 #limit to bottom of screen

    key = pygame.key.get_pressed() #check the keys that are pressed

    #if A is pressed, move left
    if key[pygame.K_a] == True or key[pygame.K_LEFT] == True:
        spaceshipRect.x -= speed

    #if D is pressed, move right
    elif key[pygame.K_d] == True or key[pygame.K_RIGHT] == True:
        spaceshipRect.x += speed

    #if S is pressed, move down
    elif key[pygame.K_s] == True or key[pygame.K_DOWN] == True:
        if spaceshipRect.y < height - spaceshipRect.height:
            spaceshipRect.y += speed

    #if W is pressed, move up
    elif key[pygame.K_w] == True or key[pygame.K_UP] == True:
        if spaceshipRect.y > limit - spaceshipRect.height:
            spaceshipRect.y -= speed

    #limit the spaceship to only move at the bottom of the screen
    if spaceshipRect.x < 0:
        spaceshipRect.x = 0

    elif spaceshipRect.y < 0:
        spaceshipRect.y = 0

    elif spaceshipRect.y > 800:
        spaceshipRect.y = 800

    elif spaceshipRect.x > 760:
        spaceshipRect.x = 760

    #display the ship on the screen
    screen.blit(spaceship,spaceshipRect)

#the laser_draw function
def laser_draw():
    
    '''
    This function draws the lasers that comes out
    of the spaceship the user controls.
    '''
    
    #load the lasers, otherwise explain the error and tell user to wait
    try:
        laser = pygame.image.load(join('images', 'Laser.png')).convert_alpha()
    except pygame.error:
        print("there was an error loading the bonus asteroid. please try again later")
        return None
    return laser

#the laser_shoot function
def laser_shoot(spaceship_rect, shoot_time, cooldown, laser_img):

    '''
    This function allows the user to shoot the laser from ship
    after pressing the spacebar.
    '''
    
    #current time in milliseconds
    current_time = pygame.time.get_ticks()    

    #if the current time subtracted from the shoot time is greater than or equal to the cooldown, then shoot the laser
    if current_time - shoot_time >= cooldown:
        key = pygame.key.get_pressed()
        #shoot laser if user presses space bar
        if key[pygame.K_SPACE]:
            laser_rect = laser_img.get_rect(midbottom =(spaceship_rect.x + spaceship_rect.width // 2, spaceship_rect.y))
            laser_bg.append(laser_rect)
            laser_sound.play()
            laser_sound.set_volume(0.3)
            shoot_time = current_time

    #return the shoot time
    return shoot_time

#the laser_update function
def laser_update(dt, laser_img):

    '''
    This function updates the position of lasers and removes them once
    they go off the screen
    '''

    #loop through the laser_bg list
    for laser in laser_bg:
        #moves the laser upward using delta time
        laser.y -= int(1000 * dt)
        #removes lasers if they go above the screen
        if laser.bottom < 0:
            laser_bg.remove(laser)
        else:
            #draws laser if on screen
            screen.blit(laser_img, laser)

#the collision function
def collision(spaceshipRect, laser_bg, font):

    '''
    This function is where the laser shoots the
    asteroids/clocks and causes them to disappear
    from the screen after the two objects collide.
    '''

    global current_score, countdown_time, final_score #access the current_score and countdown_time variables from outside the functions

    laserRemove = [] #empty list for removing the lasers after collision

    #loop through each laser in the laser list
    for laser in laser_bg:
        #create a rectangle for the laser
        laserRect = pygame.Rect(laser.x, laser.y, 10, 30)

        #loop through each asteroid in the asteroid list
        for a in asteroid_bg:
            #create an asteroid rect
            asteroidRect = pygame.Rect(a['x'], a['y'], 55, 55)
            if laserRect.colliderect(asteroidRect):
                laserRemove.append(laser) #add laser to laserRemove list upon collision
                asteroid_bg.remove(a) #remove asteroid upon collision

                #create a new asteroid to replace the one shot
                new_asteroidX = randint(0,800)
                new_asteroidY = 0
                asteroidType = choice(["asteroid1", "asteroid2"])

                #append new asteroid to the list
                asteroid_bg.append({"x": new_asteroidX, "y": new_asteroidY, "img": asteroidType})

                #if asteroid is hit, add 1 point to the score and play explosion sound
                current_score += 1
                explosion_sound.play()
                explosion_sound.set_volume(0.3)
                
                break #exits loop once collision is made

        #loop through bonus asteroid list
        for bonus in bonus_bg:
            #create a rect for bonus asteroid
            bonusRect = pygame.Rect(bonus[0], bonus[1], 55, 55)
            
            if laserRect.colliderect(bonusRect):
                laserRemove.append(laser) #add laser to laserRemove list upon collision
                bonus_bg.remove(bonus) #remove bonus asteroid upon collision

                #create a new bonus asteroid after collision
                new_bonusX = randint(0,800)
                new_bonusY = 0

                #append new bonus asteroid to list
                bonus_bg.append([new_bonusX, new_bonusY])

                #upon collision, add 10 points to player score and play explosion sound
                current_score += 10
                explosion_sound.play()
                explosion_sound.set_volume(0.3)

                break #exit loop once collision detected

        #loop through fake asteroid list
        for fake in fake_bg:
            #create a rect for fake asteroid list
            fakeRect = pygame.Rect(fake[0], fake[1], 55, 55)
            
            if laserRect.colliderect(fakeRect):
                laserRemove.append(laser) #add laser to laserRemove list upon collision
                fake_bg.remove(fake) #remove fake asteroid upon collision

                #create a new fake asteroid after collision
                new_fakeX = randint(0,800)
                new_fakeY = 0

                #append new fake asteroid to list
                fake_bg.append([new_fakeX, new_fakeY])

                #upon collision, subtract 10 seconds from player time and play explosion sound
                countdown_time -= 10
                fake_asteroid_sound.play()
                fake_asteroid_sound.set_volume(0.2)

                break #exit loop once collision detected

        #loop through clock list
        for clock in clock_bg:
            #create a clock rect
            clockRect = pygame.Rect(clock[0], clock[1], 55, 55)

            if laserRect.colliderect(clockRect):
                laserRemove.append(laser) #add laser to laserRemove list upon collision
                clock_bg.remove(clock) #remove clock from list upon collision

                #create a new clock after collision
                new_clockX = randint(0,800)
                new_clockY = 0

                #append new clock to list
                clock_bg.append([new_clockX, new_clockY])

                #upon collision, add 5 seconds to player time and play explosion sound
                countdown_time += 5
                clock_sound.play()
                clock_sound.set_volume(0.7)

                break #exit loop once collision is detected

        #set the final score equal to the current score
        final_score = current_score

    #loop through the laserRemove list
    for laser in laserRemove:
        #check if the laser is in the overall list
        if laser in laser_bg:
            laser_bg.remove(laser) #remove the laser from the list

    return True #keeps the game running

#the countdown function
def countdown(font):

    '''
    In this function, the amount of time in the timer
    is constantly decreasing.

    The function returns the remaining time from the
    timer.
    '''
    
    global countdown_time, start_time #access the variable from outside the functions

    #get the current time in milliseconds and seconds
    current_time_ms = pygame.time.get_ticks()
    current_time_s = (current_time_ms - start_time)//1000

    #calculates the remaining time
    remaining_time = max(0, countdown_time - current_time_s)

    #return the remaining time
    return remaining_time

#the draw_timer function
def draw_timer(font, remaining_time):

    '''
    This function uses the remaining time from the
    countdown function and displays a timer onto the
    screen.
    '''
    
    #obtain the minutes and seconds from the remaining time
    minutes = remaining_time // 60
    seconds = remaining_time % 60

    #display the timer on the screen
    time_str = f"{minutes:02}:{seconds:02}"
    text_surf = font.render(time_str, True, 'white')
    text_rect = text_surf.get_rect(midtop = (400, 30))
    screen.blit(text_surf, text_rect)

#the score function
def score(font):

    '''
    This function updates the players score as they
    hit the asteroids and clocks. 
    '''

    #display score on the screen
    text_surf = font.render(f"{current_score}", True, 'light green')    
    screen.blit(text_surf,(390,80))

#the statistics function
def statistics():

    '''
    This function stores the player's scores into
    a file to find the highest score.
    '''

    #access global variables
    global current_score, final_score, countdown_time

    #initialize highest score as 0
    highest_score = 0

    #ensure that the file exists
    fileExists = os.path.isfile('score.txt')
    if fileExists:
        #read the contents of score.txt
        scoreRead = open('score.txt', 'r')
        lines = scoreRead.readlines()

        #loop through each line of the file
        for score in lines:
            score = score.strip()
            if score.isdigit():
                #find the highest score
                highest_score = max(highest_score, int(score))
        scoreRead.close()

    #return the highest score
    return highest_score

#the play_button function
def play_button():

    '''
    This function draws a play button on the start screen.

    If the user clicks this button, the game begins. 
    '''

    #try the assigned font, otherwise use the default
    try:
        startFont = pygame.font.Font("fonts/SpaceMono-Bold.ttf", 50)
    except:
        startFont = pygame.font.Font(None, 50)
        
    #show the title of the game on the start screen
    startText = startFont.render("MISSION ASTEROID", True, (139, 0, 0))
    screen.blit(startText, (400 - startText.get_width()/2, 195))

    #try the assigned font, otherwise use the default
    try:
        authorFont = pygame.font.Font("fonts/SpaceMono-Regular.ttf", 30)
    except:
        authorFont = pygame.font.Font(None, 30)
        
    #display the names of the game developers
    authorText = authorFont.render("By: Grace Jowett & Sumaya Uddin", True, (160, 140, 220))
    screen.blit(authorText, (400 - authorText.get_width()/2, 250))

    authorTextShadow = authorFont.render("By: Grace Jowett & Sumaya Uddin", True, (180, 180, 200))
    screen.blit(authorText, ((400 - authorText.get_width()/2), 252))

    #play button dimensions
    buttonX = 300
    buttonY = 375
    buttonW = 200
    buttonH = 50
    buttonRadius = 15
    
    #button colors
    buttonColor = (173, 216, 230)
    textColor = (30, 30, 60)
    hoverColor = (0, 255, 204)
    
    #drawing the button
    pygame.draw.rect(screen, buttonColor, (buttonX, buttonY, buttonW, buttonH), border_radius = buttonRadius)
    
    #if user clicks play button, start the game
    pos = pygame.mouse.get_pos()
    
    if buttonX <= pos[0] <= buttonX + buttonW and buttonY <= pos[1] <= buttonY + buttonH:
        pygame.draw.rect(screen, hoverColor, (buttonX, buttonY, buttonW, buttonH), border_radius = buttonRadius)
        
        if pygame.mouse.get_pressed()[0] == 1: #left mouse click
            return True #button was clicked
    else:
        pygame.draw.rect(screen, buttonColor, (buttonX, buttonY, buttonW, buttonH), border_radius = buttonRadius)

    #font for play text
    try:
        startFont = pygame.font.Font("fonts/SpaceMono-Regular.ttf", 35)
    except:
        startFont = pygame.font.Font(None, 35)

    text_surf = startFont.render("Play", True, textColor)
    text_rect = text_surf.get_rect(center = (buttonX + buttonW//2, buttonY + buttonH//2))
    screen.blit(text_surf, text_rect)

    return False #button was not clicked

#the start_screen function
async def start_screen():
    
    '''
    This function is shows the start screen and displays
    the play button.
    '''
    
    waiting = True
    while waiting:
        #six colors for the screen
        color1 = (10, 10, 30)
        color2 = (20, 20, 50) 
        color3 = (40, 20, 60)
        color4 = (70, 60, 90)
        color5 = (230, 230, 250) 
        color6 = (35, 35, 45)

        sectionHeight = screen.get_height()//3
        
        pygame.draw.rect(screen, color1, (0, 0, screen.get_width(), sectionHeight))
        pygame.draw.rect(screen, color2, (0, sectionHeight, screen.get_width(), sectionHeight))
        pygame.draw.rect(screen, color3, (0, 0, sectionHeight * 2, sectionHeight))
        pygame.draw.rect(screen, color4, (0, sectionHeight * 2, screen.get_width()//2, sectionHeight))
        pygame.draw.rect(screen, color5, (0, sectionHeight, screen.get_width(), sectionHeight//2))
        pygame.draw.rect(screen, color6, (400, sectionHeight * 2, screen.get_width(), sectionHeight))

        #once play button is clicked, start the timer
        if play_button():
            global game_start
            game_start = pygame.time.get_ticks()
            return True #means that the button was clicked
        
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    return True #start the game is user clicks tab key
    
        pygame.display.update() #update the screen
        await asyncio.sleep(0) #wait for the next frame

    return False #button was not clicked

#the pause_button function
def pause_button(remaining_time, events):

    '''
    This function creates a pause button for the users
    to pause the game whenever they need to.
    '''
    
    global pauseFlashing, paused, countdown_time #access local variables

    #do not show the pause button if timer is less than 0
    if remaining_time <= 0:
        return
    
    #pasue button dimensions
    buttonX = 730
    buttonY = 40
    buttonW = 50
    buttonH = 50
    buttonRadius = 15
    
    #button colors
    buttonColor = (0, 0, 0, 0)
    textColor = 'white'
    hoverColor = (170, 255, 200)

    #drawing the button
    pygame.draw.rect(screen, buttonColor, (buttonX, buttonY, buttonW, buttonH), border_radius = buttonRadius)
    
    #if user clicks pause button, freeze the game
    pos = pygame.mouse.get_pos()
    if buttonX <= pos[0] <= buttonX + buttonW and buttonY <= pos[1] <= buttonY + buttonH:
        pygame.draw.rect(screen, hoverColor, (buttonX, buttonY, buttonW, buttonH), border_radius = buttonRadius)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN: #used to make sure there aren't multiple clicks each frame
                if event.button == 1: #left mouse click
                    if buttonX <= event.pos[0] <= buttonX + buttonW and buttonY <= event.pos[1] <= buttonY + buttonH:
                        pause() #call the pause function
                        return True #button was clicked
    else:
        pygame.draw.rect(screen, buttonColor, (buttonX, buttonY, buttonW, buttonH), border_radius = buttonRadius)

    #font for pause text
    try:
        pauseFont = pygame.font.Font("fonts/SpaceMono-Bold.ttf", 30)
    except:
        pauseFont = pygame.font.Font(None, 30)

    text_surf = pauseFont.render("||", True, textColor)
    text_rect = text_surf.get_rect(center = (buttonX + buttonW//2, buttonY + buttonH//2))
    screen.blit(text_surf, text_rect)

#the pause function
async def pause():

    '''
    This is the function that handles the actual pausing
    of the game. It flashes when player pauses the game and
    freezes everything as well.
    '''
    
    #access local variables
    global paused, freeze, pauseFlashing, countdown_time, pausedStart, paused_timeTotal

    #if the game is not already paused, pause it
    if not paused:
        pauseStart = pygame.time.get_ticks() #calculate the time since pause button is clicked/pressed
        freeze = screen.copy() #freeze the screen
        pauseFlashing = True #flashing the screen
        paused = True #pause button was clicked

    #flashing for the pause functionality
    flash2_time = pygame.time.get_ticks()
    while pygame.time.get_ticks() - flash2_time < 300:
        screen.fill((250,249,246))
        pygame.display.update()
        await asyncio.sleep(0)

#the resume_button function
async def resume_button(events):

    '''
    This function shows a resume button on the paused
    screen. 
    '''
    
    global pauseFlashing, unpaused #access local variables

    #if the game is not paused, the user cannot resume the game
    if not paused:
        return
    
    #resume button dimensions
    buttonX = 300
    buttonY = 300
    buttonW = 200
    buttonH = 50
    buttonRadius = 15
    
    #button colors
    buttonColor = (148, 0, 211)
    textColor = 'white'
    hoverColor = (200, 100, 255)
    
    #drawing the button
    pygame.draw.rect(screen, buttonColor, (buttonX, buttonY, buttonW, buttonH), border_radius = buttonRadius)
    
    #if user clicks resume button, continue the game
    pos = pygame.mouse.get_pos()
    if buttonX <= pos[0] <= buttonX + buttonW and buttonY <= pos[1] <= buttonY + buttonH:
        pygame.draw.rect(screen, hoverColor, (buttonX, buttonY, buttonW, buttonH), border_radius = buttonRadius)

        #if button is left clicked, call the resume function
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                await resume()
    else:
        pygame.draw.rect(screen, buttonColor, (buttonX, buttonY, buttonW, buttonH), border_radius = buttonRadius)

    #font for resume text
    try:
        resumeFont = pygame.font.Font("fonts/SpaceMono-Regular.ttf", 35)
    except:
        resumeFont = pygame.font.Font(None, 35)

    text_surf = resumeFont.render("Resume", True, textColor)
    text_rect = text_surf.get_rect(center = (buttonX + buttonW//2, buttonY + buttonH//2))
    screen.blit(text_surf, text_rect)

#the resume function
async def resume():

    '''
    This function handles the resuming of the game.

    The function unpauses the game right where the
    user left off.
    '''

    #access the local variables
    global unpaused, countdown_time, pauseFlashing, paused, pausedStart, paused_timeTotal

    #if the pausedStart variable has any time recorded, reset pausedStart    
    if pausedStart is not None:
        paused_timeTotal += pygame.time.get_ticks() - pausedStart #calculate the total paused time
        pausedStart = None

    #unpause the game and flash the screen
    paused = False
    unpaused = True
    pauseFlashing = True
    
    await asyncio.sleep(0.05)
    
    return True #button was clicked

#the restart_button function
async def restart_button(events):

    '''
    This function draws the restart button on the
    paused screen.
    '''
    
    global unpaused, flashing #access global variables

    #if the game is not paused, the user cannot restart the game
    if not paused:
        return
    
    #restart button dimensions
    buttonX = 300
    buttonY = 375
    buttonW = 200
    buttonH = 50
    buttonRadius = 15
    
    #button colors
    buttonColor = (255, 99, 71)
    textColor = 'white'
    hoverColor = (255, 69, 0)
    
    #drawing the button
    pygame.draw.rect(screen, buttonColor, (buttonX, buttonY, buttonW, buttonH), border_radius = buttonRadius)
    
    #if user clicks restart button, reset the game
    pos = pygame.mouse.get_pos()
    if buttonX <= pos[0] <= buttonX + buttonW and buttonY <= pos[1] <= buttonY + buttonH:
        pygame.draw.rect(screen, hoverColor, (buttonX, buttonY, buttonW, buttonH), border_radius = buttonRadius)

        #if user left clicks the button, restart the game
        if pygame.mouse.get_pressed()[0] == 1:
            restart() #call restart function
            return True #button was clicked
    else:
        pygame.draw.rect(screen, buttonColor, (buttonX, buttonY, buttonW, buttonH), border_radius = buttonRadius)

    #font for restart text
    try:
        restartFont = pygame.font.Font("fonts/SpaceMono-Regular.ttf", 35)
    except:
        restartFont = pygame.font.Font(None, 35)

    text_surf = restartFont.render("Restart", True, textColor)
    text_rect = text_surf.get_rect(center = (buttonX + buttonW//2, buttonY + buttonH//2))
    screen.blit(text_surf, text_rect)

#the restart function
def restart():

    '''
    This function restarts the game and resets all the
    elements once the button is clicked
    '''

    #access global variables
    global unpaused, freeze, flashing, game_start, pausedStart, paused_timeTotal, countdown_time, current_score, pausedFlashing

    #reset all of the game settings    
    flashing = True
    paused = False
    freeze = None
    pausedFlashing = False
    countdown_time = 120
    current_score = 0
    savedScore = False
    
    game_start = pygame.time.get_ticks()

    paused_timeTotal = 0
    pausedStart = None

    screen.fill('black')
    reset_game() #call reset_gane function

    pygame.display.update() #update the screen

#the flashReset function
def flashReset():

    '''
    This is a general function for the flash effect
    when restarting the game.
    '''

    global paused, flashing #access local variables

    restart() #call restart function

    paused = False #game is no longer paused
    flashing = False #stops flash from continuing after game is restarted

    #flash the screen
    screen.fill((250,249,246))
    pygame.display.update()
    
    reset_game() #call the reset_game function


#the game_over function
def game_over(remaining_time, font, events):

    '''
    This function displays the game over message,
    allows the player to play again, and shows them
    their final score as well as highest score.
    '''
    
    global flashing, final_score, savedScore #access global variables

    #if time is 00:00, display game over message
    if remaining_time <= 0:
        if current_score > 0 and not savedScore:
            allScores = open('score.txt', 'a')
            allScores.write(str(current_score) + "\n")
            allScores.close()
            savedScore = True
            
        highest_score = statistics() #call the statistics function to store the highest score
        
        gameOverText = font.render("GAME OVER!", True, (227, 28, 37))
        screen.blit(gameOverText, (400 - gameOverText.get_width()/2, 180))

        #replay button dimensions
        buttonX = 297
        buttonY = 420
        buttonW = 200
        buttonH = 50
        buttonRadius = 15

        #button colors
        buttonColor = (50, 60, 80)
        textColor = (80, 255, 100)
        hoverColor = (170, 255, 200)

        #drawing the button
        pygame.draw.rect(screen, buttonColor, (buttonX, buttonY, buttonW, buttonH), border_radius = buttonRadius)

        #if user clicks replay button, flash the screen
        pos = pygame.mouse.get_pos()
        if buttonX <= pos[0] <= buttonX + buttonW and buttonY <= pos[1] <= buttonY + buttonH:
            pygame.draw.rect(screen, hoverColor, (buttonX, buttonY, buttonW, buttonH), border_radius = buttonRadius)

            if pygame.mouse.get_pressed()[0] == 1:
                flashReset()
                reset_game()
                return True
        else:
            pygame.draw.rect(screen, buttonColor, (buttonX, buttonY, buttonW, buttonH), border_radius = buttonRadius)

        #font for replay text
        try:
            replayFont = pygame.font.Font("fonts/SpaceMono-Regular.ttf", 35)
        except:
            replayFont = pygame.font.Font(None, 35)

        text_surf = replayFont.render("Replay", True, textColor)
        text_rect = text_surf.get_rect(center = (buttonX + buttonW/2, buttonY + buttonH/2))
        screen.blit(text_surf, text_rect)

        #display the final score
        try:
            final_score_text = pygame.font.Font("fonts/SpaceMono-Regular.ttf", 30)
        except:
            final_score_text = pygame.font.Font(None, 30)

        finalScoreFont = final_score_text.render(f'Final Score: {final_score}', True, "light gray")
        screen.blit(finalScoreFont, (400 - finalScoreFont.get_width()/2, 260))

        #display the highest score
        try:
            high_score_text = pygame.font.Font("fonts/SpaceMono-Regular.ttf", 30)
        except:
            high_score_text = pygame.font.Font(None, 30)

        highScoreFont = high_score_text.render(f'Highest Score: {highest_score}', True, "gold")
        screen.blit(highScoreFont, (400 - highScoreFont.get_width()/2, 310))

#the reset_game function
def reset_game():

    '''
    This function restarts everything, and redraws them
    after the flash. This gives the player a clean slate
    to try and beat their previous score.
    '''
    
    #access global variables
    global countdown_time, current_score, start_time, savedScore, game_start, pasued_totalTime, pausedStart

    #start the game again and reset any paused durations
    game_start = pygame.time.get_ticks()
    paused_timeTotal = 0
    pausedStart = None
    
    savedScore = False #allow a new score to be saved after reset
    
    #reset the time and score
    countdown_time = 120
    start_time = pygame.time.get_ticks()
    current_score = 0

    #clear the lists
    star_bg.clear()
    asteroid_bg.clear()
    bonus_bg.clear()
    fake_bg.clear()
    laser_bg.clear()
    clock_bg.clear()

    #redraw all the elements
    spaceship, spaceshipRect = spaceship_draw()
    star_img = star() 
    asteroid1_img, asteroid2_img = asteroid()
    bonus_img = bonus_asteroid()
    fake_img = fake_asteroid()
    laser_img = laser_draw()
    clock_img = extra_time() 

#call the main function
asyncio.run(main())