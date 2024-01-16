import { Injectable } from '@angular/core';
import { environment } from 'src/environments/environment';
import { HttpClient } from "@angular/common/http";
import { TrainingDates } from '../types';

@Injectable({
  providedIn: 'root'
})
export class ForecastService {

  constructor(private http: HttpClient) { }

  uploadFiles(formData : FormData) {
    return this.http.post<FormData>(environment.forecastServerURL + '/api/forecast-data', formData);
  }

  trainModel(formData: FormData) {
    return this.http.post<FormData>(environment.forecastServerURL + '/api/model/train', formData);
  }

  getModels() {
    return this.http.get(environment.forecastServerURL);
  }

  test(formData: FormData) {
    return this.http.post<Ret>(environment.forecastServerURL + '/api/forecast-data/predict', formData);
  }
}

interface Ret {
  data: [];
  dates: [];
}