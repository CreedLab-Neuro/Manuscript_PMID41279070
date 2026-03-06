Pre-processing photometry in Data\MasonPhotometry\Pavlovian\RWD\Fluorescence.  
1. We pre-processed data to do qc, motion correction and z-score of the full trace - stored in Processed_df  
Preprocessing https://colab.research.google.com/drive/11lXbswpBkk24Ruhv_2vUWffnuOfMujLK?usp=sharing
2. We processed the "Events" column of each Fluorescence file to create new columns on Processed_df with 0s and 1s for ToneStart, ToneEnd, Pellet Grab  
  
Pre-processing Bonsai tracking - Data is in \Data\MasonPhotometry\Pavlovian\Bonsai  
3. We imported and synchronized the Bonsai tracking X, Y data, and Event timestamps  
4. Initially align based on the first ToneStart   
5. Identify Bonsai Events and plot two strip plots - RWD Tones, Bonsai Tones - use this to design an alignment strategy  
5. Import X, Y, and Events into columns in Processed_df labeled "Bonsai_X", "Bonsai_Y", "Bonsai_ToneStart"  
6. Check the alignment between RWD and Bonsai tones - quantify the differences, see if we can scrunch to improve this  
7. Scale Bonsai_X, Bonsai_Y to the box size (18cm x 36cm)  
8. Generate Speed, and Distance_from_FED based on Bonsai_X and Bonsai_Y  
  
Event code:  
100ms is Tone  
500ms is Pellet Grab  
All of this data had 5s tones  

Goal:  
One file per mouse containing processed photometry, RWD events, Bonsai Tracking/Speed/Distance_To_FED, and Bonsai events (largely redundant with RWD events but lets us examine the synchronization error)  
