import { Component } from '@angular/core';
import {Data, Color} from 'plotly.js';
import { Papa } from 'ngx-papaparse';
import { HttpClient } from '@angular/common/http';
import { parse } from 'querystring';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'Magic Visualizer';
  data: Data[];
  x: number[];
  y: number[];
  name: string[];
  color: Color[]
  layout: any;
  constructor(
    private papa: Papa,
    private http: HttpClient
  ){}

  ngOnInit(){
    this.http.get('../assets/data/PCA2dGraphPoints.csv', {responseType: 'text'})
    .subscribe(
      data => {
        let parsed = this.papa.parse(data, {header: true});
        this.x = [];
        this.y = [];
        this.name = [];
        this.color = [];
        let d = this.getRandomSubarray(parsed.data, 19000);
        let minx = 0;
        let miny = 0;
        for (let elem of d){
          let x = parseFloat(elem.x);
          let y = parseFloat(elem.y);
          if (x < minx){ minx = x}
          if (y < miny){ miny = y}
          this.x.push(x);
          this.y.push(y);
          this.name.push(elem.name);
          this.color.push(elem.color);
        }
        miny = miny * -1;
        minx = minx * -1
        this.y = this.y.map(elem => { return elem + miny})
        this.x = this.x.map(elem => { return elem + minx})
        console.log(this.x);
        this.buildGraph()
      },
      error => {
        console.log(error);
      }
    );
  }

  getRandomSubarray(arr, size) {
    var shuffled = arr.slice(0), i = arr.length, temp, index;
    while (i--) {
        index = Math.floor((i + 1) * Math.random());
        temp = shuffled[index];
        shuffled[index] = shuffled[i];
        shuffled[i] = temp;
    }
    return shuffled.slice(0, size);
}

  buildGraph(){
    let marker: any = {
      color: this.color,
      size: 8,
    }

    var trace1: Data = {
      x: this.x,
      y: this.y,
      mode: 'markers',
      type: 'scatter',
      marker: marker,
      text: this.name,
    };
    
    this.data = [trace1];
    
    this.layout = {
      title: 'Test Graph'
    };

  }
}
