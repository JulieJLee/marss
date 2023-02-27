/************************************************************************
 *
 *  snr.c, part of tmn (TMN encoder)
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

#include"sim.h"

#include<math.h>

/**********************************************************************
 *
 *	Name:        SNRcomp
 *	Description:        Compares two image files using SNR
 *                      No conversion to 422
 *	
 *	Input:	      
 *	Returns:       
 *	Side effects:
 *
 *	Date: 930711	Author: Karl.Lillevold@nta.no
 *
 ***********************************************************************/



void ComputeSNR(PictImage *im1, PictImage *im2, Results *res, int write)
{
  FILE *out = NULL;
  int n;
  register int m;
  int quad, quad_Cr, quad_Cb, diff;
  PictImage *diff_image = NULL;
  /* Diff. image written to diff_filename */
  char *diff_filename=DEF_DIFFILENAME;

  if (write) {
    out = fopen(diff_filename,"ab");
    diff_image = (PictImage *)malloc(sizeof(PictImage));
    diff_image->lum = (unsigned char *)malloc(sizeof(char)*pels*lines);
    diff_image->Cr =  (unsigned char *)malloc(sizeof(char)*pels*lines/4);
    diff_image->Cb =  (unsigned char *)malloc(sizeof(char)*pels*lines/4);    
  }

  quad = 0;
  quad_Cr = quad_Cb = 0;
  /* Luminance */
  quad = 0;
  for (n = 0; n < lines; n++)
    for (m = 0; m < pels; m++) {
      diff = *(im1->lum + m + n*pels) - *(im2->lum + m + n*pels);
      if (write)
        *(diff_image->lum + m + n*pels) = 10*diff + 128;
      quad += diff * diff;
    }

  res->SNR_l = (float)quad/(float)(pels*lines);
  if (res->SNR_l) {
    res->SNR_l = (float)(255*255) / res->SNR_l;
    res->SNR_l = 10 * (float)log10(res->SNR_l);
  }
  else res->SNR_l = (float)99.99;

  /* Chrominance */
  for (n = 0; n < lines/2; n++)
    for (m = 0; m < pels/2; m++) {
      quad_Cr += (*(im1->Cr+m + n*pels/2) - *(im2->Cr + m + n*pels/2)) *
        (*(im1->Cr+m + n*pels/2) - *(im2->Cr + m + n*pels/2));
      quad_Cb += (*(im1->Cb+m + n*pels/2) - *(im2->Cb + m + n*pels/2)) *
        (*(im1->Cb+m + n*pels/2) - *(im2->Cb + m + n*pels/2));
      if (write) {
        *(diff_image->Cr + m + n*pels/2) = 
          (*(im1->Cr+m + n*pels/2) - *(im2->Cr + m + n*pels/2))*10+128;
        *(diff_image->Cb + m + n*pels/2) = 
          (*(im1->Cb+m + n*pels/2) - *(im2->Cb + m + n*pels/2))*10+128;
      }
    }

  res->SNR_Cr = (float)quad_Cr/(float)(pels*lines/4);
  if (res->SNR_Cr) {
    res->SNR_Cr = (float)(255*255) / res->SNR_Cr;
    res->SNR_Cr = 10 * (float)log10(res->SNR_Cr);
  }
  else res->SNR_Cr = (float)99.99;

  res->SNR_Cb = (float)quad_Cb/(float)(pels*lines/4);
  if (res->SNR_Cb) {
    res->SNR_Cb = (float)(255*255) / res->SNR_Cb;
    res->SNR_Cb = 10 * (float)log10(res->SNR_Cb);
  }
  else res->SNR_Cb = (float)99.99;

  if (write) {
    fwrite(diff_image->lum, sizeof(char), pels*lines, out);
    fwrite(diff_image->Cr,  sizeof(char), pels*lines/4, out);
    fwrite(diff_image->Cb,  sizeof(char), pels*lines/4, out);
    free(diff_image->lum);
    free(diff_image->Cr);
    free(diff_image->Cb);
    free(diff_image);
    fclose(out);
  }
  return;
}

