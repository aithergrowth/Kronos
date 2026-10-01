//+------------------------------------------------------------------+
//| KronosForecast.mq5                                                |
//| Draws the Kronos forecast written by kronos_trader on the chart.  |
//| The Python loop writes Common\Files\kronos_forecast_<SYMBOL>.csv  |
//| (one line per future candle: time;open;high;low;close in server  |
//| time, epoch seconds), plus a header line "# direction;confidence; |
//| pct_change;expected_high;expected_low". This indicator re-reads   |
//| it every RefreshSeconds and draws the mean path, the expected     |
//| band and a label to the right of the last candle.                 |
//| Enable "Chart shift" (the arrow icon) to see the space on the     |
//| right. It draws only; it never trades.                            |
//+------------------------------------------------------------------+
#property copyright "kronos_trader"
#property version   "1.00"
#property indicator_chart_window
#property indicator_plots 0

input int    RefreshSeconds = 30;          // how often the file is re-read
input color  PathColor      = clrSteelBlue; // mean path
input color  BandColor      = C'222,232,242'; // expected high / low band
input string FilePrefix     = "kronos_forecast_";

string prefix = "KF_";

int OnInit()
{
   EventSetTimer(RefreshSeconds);
   Redraw();
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   ObjectsDeleteAll(0, prefix);
}

int OnCalculate(const int rates_total, const int prev_calculated, const datetime &time[], const double &open[],
                const double &high[], const double &low[], const double &close[], const long &tick_volume[],
                const long &volume[], const int &spread[])
{
   return(rates_total);
}

void OnTimer()
{
   Redraw();
}

void Redraw()
{
   string name = FilePrefix + _Symbol + ".csv";
   int h = FileOpen(name, FILE_READ | FILE_TXT | FILE_ANSI | FILE_COMMON);
   if(h == INVALID_HANDLE)
      return;
   ObjectsDeleteAll(0, prefix);
   datetime t_prev = 0; double c_prev = 0.0;
   string direction = ""; double confidence = 0.0, pct = 0.0, band_high = 0.0, band_low = 0.0;
   datetime t_first = 0, t_last = 0; int k = 0;
   while(!FileIsEnding(h))
   {
      string line = FileReadString(h);
      if(StringLen(line) == 0) continue;
      string parts[];
      if(StringGetCharacter(line, 0) == '#')
      {
         StringSplit(StringSubstr(line, 1), ';', parts);
         if(ArraySize(parts) >= 5)
         {
            direction = parts[0]; confidence = StringToDouble(parts[1]); pct = StringToDouble(parts[2]);
            band_high = StringToDouble(parts[3]); band_low = StringToDouble(parts[4]);
         }
         continue;
      }
      if(StringSplit(line, ';', parts) < 5) continue;
      datetime t = (datetime)StringToInteger(parts[0]);
      double c = StringToDouble(parts[4]);
      if(k == 0) { t_first = t; t_prev = t; c_prev = iClose(_Symbol, _Period, 0); }
      string seg = prefix + "path_" + IntegerToString(k);
      ObjectCreate(0, seg, OBJ_TREND, 0, t_prev, c_prev, t, c);
      ObjectSetInteger(0, seg, OBJPROP_COLOR, PathColor);
      ObjectSetInteger(0, seg, OBJPROP_WIDTH, 2);
      ObjectSetInteger(0, seg, OBJPROP_RAY_RIGHT, false);
      ObjectSetInteger(0, seg, OBJPROP_SELECTABLE, false);
      t_prev = t; c_prev = c; t_last = t; k++;
   }
   FileClose(h);
   if(k == 0) return;
   if(band_high > band_low)
   {
      string band = prefix + "band";
      ObjectCreate(0, band, OBJ_RECTANGLE, 0, t_first, band_low, t_last, band_high);
      ObjectSetInteger(0, band, OBJPROP_COLOR, BandColor);
      ObjectSetInteger(0, band, OBJPROP_FILL, true);
      ObjectSetInteger(0, band, OBJPROP_BACK, true);
      ObjectSetInteger(0, band, OBJPROP_SELECTABLE, false);
   }
   string label = prefix + "label";
   ObjectCreate(0, label, OBJ_TEXT, 0, t_last, band_high > 0 ? band_high : c_prev);
   ObjectSetString(0, label, OBJPROP_TEXT, StringFormat("Kronos %s %.0f%%  %+.2f%%", direction, confidence * 100.0, pct));
   ObjectSetInteger(0, label, OBJPROP_COLOR, PathColor);
   ObjectSetInteger(0, label, OBJPROP_FONTSIZE, 8);
   ObjectSetInteger(0, label, OBJPROP_ANCHOR, ANCHOR_LEFT_LOWER);
   ChartRedraw(0);
}
//+------------------------------------------------------------------+
