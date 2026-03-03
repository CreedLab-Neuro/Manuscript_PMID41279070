/*
  Feeding experimentation device 3 (FED3)
  Bandit task

  This example shows a simple 2-armed bandit task. Here, the reward probabilities of left and right 
  always add 100, and change simultaneously. Thus, this is a special case of the 2-armed bandit task 
  that is equivalent to a probabilistic reversal task. 

  Code written by alexxai@wustl.edu and meaghan.creed@wustl.edu and alegariamacal@wustl.edu
  June, 2023

  This project is released under the terms of the Creative Commons - Attribution - ShareAlike 3.0 license:
  human readable: https://creativecommons.org/licenses/by-sa/3.0/
  legal wording: https://creativecommons.org/licenses/by-sa/3.0/legalcode
  Copyright (c) 2020 Lex Kravitz
*/

#include <FED3.h>          //Include the FED3 library
String sketch = "Bandit";  //Unique identifier text for each sketch, change string only.
FED3 fed3(sketch);         //Start the FED3 object - don't change

int pellet_counter = 0;                     //pellet counter variable
int timeoutIncorrect = 10;                  //timeout duration in seconds, set to 0 to remove the timeout
int probs[6] = {10,40,60,90,65,35};  //****Reward probability options
int new_prob_left = 10;
int new_prob_right = 40;
String last_poke = "";


void setup() {
  fed3.countAllPokes = false;
  fed3.LoRaTransmit = false;
  fed3.pelletsToSwitch = 15;      // Number of pellets required to finish the block and change reward probabilities
  fed3.prob_left = 10;            // Initial reward probability of left poke
  fed3.prob_right = 40;           // ****Initial reward probability of right poke
  fed3.allowBlockRepeat = false;  // ****Whether the same probabilities can be used for two blocks in a row
  fed3.begin();                   // Setup the FED3 hardware, all pinmode screen etc, initialize SD card
}

void loop() {
  //////////////////////////////////////////////////////////////////////////////////
  //  This is the main bandit task. In general it will be composed of three parts:
  //  1. Set up conditions to trigger a change in reward probabilities
  //  2. Set up behavior upon a left poke
  //  3. Set up behavior upon a right poke
  //////////////////////////////////////////////////////////////////////////////////
  fed3.run();  //Call fed.run at least once per loop

  // This is part 1. In this example, reward probabilities will be switched when 30 rewards
  // (value of fed3.pelletsToswitch assigned in line 35) are obtained. Notice that in this example
  // the reward probability of left + reward probability of right always add to 100. Additionally
  // in this example, the reward probabilities in the new block are not allowed to be the same to
  // the reward probability of the previous block.
  if (pellet_counter == fed3.pelletsToSwitch) {
    pellet_counter = 0;
    new_prob_left = probs[random(0, 6)];
    if (!fed3.allowBlockRepeat) {
      while (new_prob_left == fed3.prob_left) {
        new_prob_left = probs[random(0, 6)];
      }
      fed3.prob_left = new_prob_left;
      
      if (new_prob_left == 10) {
        new_prob_right = 40;
      }
      else if (new_prob_left == 40) {
        new_prob_right = 10;
      }
      else if (new_prob_left == 60) {
        new_prob_right = 90;
      }
      else if (new_prob_left == 90) {
        new_prob_right = 60;
      }
      else if(new_prob_left == 65) {
        new_prob_right = 35;
      }
      else if (new_prob_left == 35) {
        new_prob_right = 65;
      }
      fed3.prob_right = new_prob_right;
    }
    
  } else {
    if (new_prob_left == 10) {
        new_prob_right = 40;
    }
    if (new_prob_left == 40) {
      new_prob_right = 10;
    }
    if (new_prob_left == 60) {
      new_prob_right = 90;
    }
    if (new_prob_left == 90) {
      new_prob_right = 60;
    }
    if(new_prob_left == 65) {
      new_prob_right = 35;
    }
    if (new_prob_left == 35) {
      new_prob_right = 65;
    }
    fed3.prob_left = new_prob_left;
    fed3.prob_right = new_prob_right;
  }
  





  // This is part 2. This is the behavior of the task after a left poke.
  // Notice that in this example pellet_counter only increases if a pellet
  // was actually delivered (fed.Feed() is called). Additionally, the timeout
  // resets if the mouse pokes during timeout, and also white noise is present
  // through the whole timeout
  if (fed3.Left) {
    fed3.BlockPelletCount = pellet_counter;
    fed3.logLeftPoke();  //Log left poke
    delay(1000);
    if (random(100) < fed3.prob_left) {  //Select a random number between 0-100 and ask if it is between 0-80 (80% of the time).  If so:
      fed3.ConditionedStimulus();        //Deliver conditioned stimulus (tone and lights)
      fed3.Feed();                       //Deliver pellet
      pellet_counter++;                  //Increase pellet counter by one
  }  else {                             //If random number is between 81-100 (20% of the time)
      fed3.Tone(300, 600);               //Play the error tone
      fed3.Timeout(timeoutIncorrect, false, true);
    }
    last_poke = "Left";
  }

  // This is part 3. This is the behavior of the task after a right poke.
  // Notice that in this example the behavior after a right poke is exactly the
  // same as the the behvaior after a left poke.
  if (fed3.Right) {
    fed3.BlockPelletCount = pellet_counter;
    fed3.logRightPoke();  //Log Right poke
    delay(1000);
    if (random(100) < fed3.prob_right) {  //Select a random number between 0-100 and ask if it is between 80-100 (20% of the time).  If so:
      fed3.ConditionedStimulus();         //Deliver conditioned stimulus (tone and lights)
      fed3.Feed();                        //Deliver pellet
      pellet_counter++;                   //Increase pellet counter by one
    } else {                              //If random number is between 0-80 (80% of the time)
      fed3.Tone(300, 600);                //Play the error tone
      fed3.Timeout(timeoutIncorrect, false, true);
    }
    last_poke = "Right";
  }
}
