/************************************************************************
 *
 *  io.c, part of tmn (TMN encoder)
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

/**********************************************************************
 *
 *	Name:        ReadImage        
 *	Description:	Reads one raw image from disk
 *	
 *	Input:        filename of sequence, frame no. to be read,
 *        headerlength of sequence
 *	Returns:	Pointer to start of raw YUV-data
 *	Side effects:	Memory allocated to image-data
 *
 *	Date: 940108	Author:	Karl.Lillevold@nta.no
 *
 ***********************************************************************/

unsigned char *ReadImage(char *filename, int frame_no, int headerlength)

{
  FILE *im_file = NULL;
  int im_size = pels*lines*3/2;
  unsigned char *raw;
  int status;

  if ((raw = (unsigned char *)malloc(sizeof(char)*im_size)) == NULL) {
    fprintf(stderr,"Couldn't allocate memory to image\n");
    exit(-1);
  }
  if ((im_file = fopen(filename,"rb")) == NULL) {
    fprintf(stderr,"Unable to open image_file: %s\n",filename);
    exit(-1);
  }
  rewind(im_file);
  /* Find the correct image */
  status = fseek(im_file,headerlength + (frame_no) * im_size,0);
  if (status != 0) {
    fprintf(stderr,"Error in seeking image no: %d\n",frame_no);
    fprintf(stderr,"From file: %s\n",filename);
    exit(-1);
  }
  /* Read image */
  fprintf(stdout,"Reading image no: %d\n",frame_no);
  if ((status = fread(raw, sizeof(char), 
              im_size, im_file)) != im_size) {
    fprintf(stderr,"Error in reading image no: %d\n",frame_no);
    fprintf(stderr,"From file: %s\n",filename);
    exit(-1);
  }

  fclose(im_file);
  return raw;
}

/**********************************************************************
 *
 *	Name:        FillImage
 *	Description:	fills Y, Cb and Cr of a PictImage struct
 *	
 *	Input:        pointer to raw image
 *        
 *	Returns:	pointer to filled PictImage
 *	Side effects:	allocates memory to PictImage
 *                      raw image is freed
 *
 *	Date: 940109	Author:	Karl.Lillevold@nta.no
 *
 ***********************************************************************/

PictImage *FillImage(unsigned char *in)
{
  PictImage *Pict;

  Pict = InitImage(pels*lines);

  memcpy(Pict->lum, in, pels*lines);
  memcpy(Pict->Cb, in + pels*lines, pels*lines/4);
  memcpy(Pict->Cr, in + pels*lines + pels*lines/4, pels*lines/4);

  free(in);
  return(Pict);
}

/**********************************************************************
 *
 *	Name:        WriteImage
 *	Description:	Writes PictImage struct to disk
 *	
 *	Input:        pointer to image data to be stored, filename
 *        to be used on the disk, image size
 *	Returns:	
 *	Side effects:	
 *
 *	Date: 930115	Author: Karl.Lillevold@nta.no
 *
 ***********************************************************************/

void WriteImage(PictImage *image, char *filename)

{
  int status;
  FILE *f_out;

  /* Opening file */
  if ((f_out = fopen(filename,"ab")) == NULL) {
    fprintf(stderr,"%s%s\n","Error in opening file: ",filename);
    exit(-1);
  }

  /* Writing lum to file */
  if ((status = fwrite(image->lum,sizeof(char),pels*lines,f_out)) 
      != pels*lines) {
    fprintf(stderr,"%s%s\n","Error in writing to file: ",filename);
    exit(-1);
  }
  /* Writing Cb to file */
  if ((status = fwrite(image->Cb,sizeof(char),pels*lines/4,f_out)) 
      != pels*lines/4) {
    fprintf(stderr,"%s%s\n","Error in writing to file: ",filename);
    exit(-1);
  }
  /* Writing Cr to file */
  if ((status = fwrite(image->Cr,sizeof(char),pels*lines/4,f_out)) 
      != pels*lines/4) {
    fprintf(stderr,"%s%s\n","Error in writing to file: ",filename);
    exit(-1);
  }

  fclose(f_out);
  return;
}


/**********************************************************************
 *
 *	Name:        InitImage
 *	Description:	Allocates memory for structure of 4:2:0-image
 *	
 *	Input:	        image size
 *	Returns:	pointer to new structure
 *	Side effects:	memory allocated to structure
 *
 *	Date: 930115        Author: Karl.Lillevold@nta.no
 *
 ***********************************************************************/

PictImage *InitImage(int size)
{
  PictImage *new;

  if ((new = (PictImage *)malloc(sizeof(PictImage))) == NULL) {
    fprintf(stderr,"Couldn't allocate (PictImage *)\n");
    exit(-1);
  }
  if ((new->lum = (unsigned char *)malloc(sizeof(char)*size)) 
      == NULL) {
    fprintf(stderr,"Couldn't allocate memory for luminance\n");
    exit(-1);
  }
  if ((new->Cr = (unsigned char *)malloc(sizeof(char)*size/4)) 
      == NULL) {
    fprintf(stderr,"Couldn't allocate memory for Cr\n");
    exit(-1);
  }
  if ((new->Cb = (unsigned char *)malloc(sizeof(char)*size/4)) 
      == NULL) {
    fprintf(stderr,"Couldn't allocate memory for Cb\n");
    exit(-1);
  }

  return new;
}


/**********************************************************************
 *
 *	Name:        FreeImage
 *	Description:	Frees memory allocated to structure of 4:2:0-image
 *	
 *	Input:        pointer to structure
 *	Returns:
 *	Side effects:	memory of structure freed
 *
 *	Date: 930115	Author: Karl.Lillevold@nta.no
 *
 ***********************************************************************/

void FreeImage(PictImage *image)

{
  free(image->lum);
  free(image->Cr);
  free(image->Cb);
  free(image);
}

