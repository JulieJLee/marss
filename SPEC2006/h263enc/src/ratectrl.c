/************************************************************************
 *
 *  ratectrl.c, part of tmn (TMN encoder)
 *  Copyright (C) 1996  Telenor R&D, Norway
 *        Karl Olav Lillevold <Karl.Lillevold@nta.no>
 *
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program; if not, write to the Free Software
 *  Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
 *
 *  Karl Olav Lillevold               <Karl.Lillevold@nta.no>
 *  Telenor Research and Development
 *  P.O.Box 83                        tel.:   +47 63 84 84 00
 *  N-2007 Kjeller, Norway            fax.:   +47 63 81 00 76
 *
 *  Robert Danielsen                  e-mail: Robert.Danielsen@nta.no
 *  Telenor Research and Development  www:    http://www.nta.no/brukere/DVC/
 *  P.O.Box 83                        tel.:   +47 63 84 84 00
 *  N-2007 Kjeller, Norway            fax.:   +47 63 81 00 76
 *  
 ************************************************************************/

/* IMPORTANT NOTE: 

   The H.263 standard does not specify a rate control method.  Each
   H.263 encoder has to implement a rate control suited for what the
   encoder is going to be used for. This software now includes two
   rate control methods: (i) the rate control from the TMN5 document,
   and (ii) the rate control method used to encode the H.263
   bitstreams submitted to the MPEG-4 tests. The default rate control
   is (i) which is suitable for low-delay teleconferencing. If the
   software is compiled with the OFFLINE_RATE_CONTROL flag, (ii) will
   be used. Read more about (ii) below.

   */

#include "sim.h"

#ifdef OFFLINE_RATE_CONTROL
 
/* ABOUT THE OFFLINE RATE CONTROL:

   If you compile the TMN encoder with OFFLINE_RATE_CONTROL, you will
   get the same rate control as was used to generate the MPEG-4
   anchors. This rate control does not skip any extra pictures after
   the first frame, and it uses a fixed frame rate. It is possible to
   start the rate control after a certain percentage of the sequence
   has been encoded with a fixed quantization parameter. Its purpose
   is to achieve the target bitrate as a mean bitrate for the whole
   sequence. In other words, it is a rate control method optimized for
   offline compression.

   If oyu use the offline rate control, you will risk not achieving
   the target rate under one or more of the following conditions :
   
   (i)   too high frame rate 
   (ii)  too low start value for the quantization parameter
   (iii) the rate control is started too late
   (iv)  the sequence encoded is too short

*/



#include <stdio.h>
#include <math.h>


/**********************************************************************
 *
 *	Name:	        FrameUpdateQP
 *	Description:    updates quantizer once per frame for 
 *                      simplified rate control
 *	
 *      Returns:        new quantizer
 *	Side effects:
 *
 *	Date: 950910	Author: Karl.Lillevold@nta.no
 *
 ***********************************************************************/

int FrameUpdateQP(int buf, int bits, int frames_left, int QP, int B, 
          float seconds) 
{
  int newQP, dQP;
  float buf_rest, buf_rest_pic;

  buf_rest = seconds * B - (float)buf;

  newQP = QP;

  if (frames_left > 0) {
    buf_rest_pic = buf_rest / (float)frames_left;

    printf("\n");
    printf("  Simplified rate control for %d remaining pictures:\n",
           frames_left);
    printf("  Bits spent / left       : %8d / %d (%d per picture)\n", 
           buf, mnint(buf_rest), mnint(buf_rest_pic));

    dQP = mmax(1,QP*0.1);

    printf("  Limits                  : %8.0f / %.0f\n", 
           buf_rest_pic / 1.15, buf_rest_pic * 1.15);
    printf("  Bits spent on last frame: %8d\n", bits);

    if (bits > buf_rest_pic * 1.15) {
      newQP = mmin(31,QP+dQP);
      printf("  QP -> new QP            : %2d -> %2d\n", QP, newQP);
    }
    else if (bits < buf_rest_pic / 1.15) {
      newQP = mmax(1,QP-dQP);
      printf("  QP -> new QP            : %2d -> %2d\n", QP, newQP);
    }
    else {
      printf("  QP not changed\n");
    }
  }
  printf("\n");
  return newQP;
}

#else

/* 

   These routines are needed for the low-delay , variable frame rate,
   rate control specified in the TMN5 document

*/

#include <math.h>

/* rate control static variables */

static float B_prev;     /* number of bits spent for the previous frame */
static float B_target;   /* target number of bits/picture               */
static float global_adj; /* due to bits spent for the previous frame    */


void InitializeRateControl()
{
  B_prev = (float)0.0;
}

void UpdateRateControl(int bits)
{
  B_prev = (float)bits;
}

int InitializeQuantizer(int pict_type, float bit_rate, 
        float target_frame_rate, float QP_mean) 

/* QP_mean = mean quantizer parameter for the previous picture */
/* bitcount = current total bit count                          */
/* To calculate bitcount in coder.c, do something like this :  */
/* int bitcount;                                               */
/* AddBitsPicture(bits);                                       */
/* bitcount = bits->total;                                     */

{
  int newQP;

  if (pict_type == PCT_INTER) {

    B_target = bit_rate / target_frame_rate;

    /* compute picture buffer descrepency as of the previous picture */

    if (B_prev != 0.0) {
      global_adj = (B_prev - B_target) / (2*B_target);
    }
    else {
      global_adj = (float)0.0;
    }
    newQP = (int)(QP_mean * (1 + global_adj) + (float)0.5);
    newQP = mmax(1,mmin(31,newQP));  
  }
  else if (pict_type == PCT_INTRA) {
    fprintf(stderr,"No need to call InititializeQuantizer() for Intra picture\n");
    exit(-1);
  }
  else  {
    fprintf(stderr,"Error (InitializePictureRate): picture type unkown.\n");
    exit(-1);
  }  
#if 1
  printf("Global adj = %.2f\n", global_adj);
  printf("meanQP = %.2f   newQP = %d\n", QP_mean, newQP);
#endif
  fprintf(stdout,"Target no. of bits: %.2f\n", B_target);

  return newQP;
}


/*********************************************************************
*   Name:          UpdateQuantizer
*
*
* Description: This function generates a new quantizer step size based
*                  on bits spent up until current macroblock and bits
*                  spent from the previous picture.  Note: this
*                  routine should be called at the beginning of each
*                  macroblock line as specified by TMN4. However, this
*                  can be done at any macroblock if so desired.
*
*  Input: current macroblock number (raster scan), mean quantizer
*  paramter for previous picture, bit rate, source frame rate,
*  hor. number of macroblocks, vertical number of macroblocks, total #
*  of bits used until now in the current picture.
*
*  Returns: Returns a new quantizer step size for the use of current
*  macroblock Note: adjustment to fit with 2-bit DQUANT should be done
*  in the calling program.
*
*  Side Effects:  
*
*  Date: 1/5/95    Author: Anurag Bist
*
**********************************************************************/


int UpdateQuantizer(int mb, float QP_mean, int pict_type, float bit_rate, 
                    int mb_width, int mb_height, int bitcount) 

/* mb = macroblock index number */
/* QP_mean = mean quantizer parameter for the previous picture */
/* bitcount = total # of bits used until now in the current picture */

{
  int newQP=16;
  float local_adj, descrepency, projection;
  
  if (pict_type == PCT_INTRA) {
    newQP = 16;
  }
  else if (pict_type == PCT_INTER) {
    /* compute expected buffer fullness */
    
    projection = mb * (B_target / (mb_width*mb_height));
    
    /* measure descrepency between current fullness and projection */
    descrepency= (bitcount - projection);
    
    /* scale */
    
    local_adj = 12 * descrepency / bit_rate;
    
#if 0
    printf("mb = %d\n",mb);
    printf("bit_count = %d projection = %.2f \n",bitcount,projection);
    printf("B_target = %.2f local_adj = %.2f \n",B_target,local_adj);
#endif
    
    newQP = (int)(QP_mean * (1 + global_adj + local_adj) + 0.5);
    
  /* the update equation for newQP in TMN4 document section 3.7 */

  }
  else  {
    fprintf(stderr,"Error (UpdateQuantizer): picture type unkown.\n");
  }
  
#if 0
  printf("mb = %d  newQP = %d \n",mb,newQP);
#endif 

  newQP = mmax(1,mmin(31,newQP));  
  return newQP;
}

#endif
