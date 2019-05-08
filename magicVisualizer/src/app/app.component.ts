import { Component, EventEmitter, Output, ViewChild, ElementRef } from '@angular/core';
import {Data, Color} from 'plotly.js';
import { Papa } from 'ngx-papaparse';
import { HttpClient } from '@angular/common/http';
import { Subject } from "rxjs";
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { element } from '@angular/core/src/render3';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'Magic Visualizer';
  dataUrl = '../assets/data/PCA2dGraphPoints.csv';
  data: Data[];
  displayNum: number = 3000;
  selectedBtn: string = "pca";
  x: number[];
  y: number[];
  name: string[];
  color: Color[];
  layout: any;
  @ViewChild('sample') sampleRef: ElementRef;
  @Output() sampleSizeEmitter: EventEmitter<number> = new EventEmitter();  
  debouncer: Subject<number> = new Subject();
  constructor(
    private papa: Papa,
    private http: HttpClient,
  ){
    this.sampleSizeEmitter.pipe(debounceTime(300))
    .subscribe((val) => {
      if (val != NaN && val != this.displayNum){
        this.displayNum = Number.parseInt(this.sampleRef.nativeElement.value); 
        if (this.selectedBtn == 'blend') { 
          this.buildAvg('../assets/data/TSNE2dGraphPoints.csv','../assets/data/SpectralEmbeddingRBF2dGraphPoints.csv');
        } else { this.getGraphData(); }
      }
    });
  }

  ngOnInit(){
    this.getGraphData();
  }

  buildAvg(url1, url2){
    let weight = 1;
    let walk_tolerance = .8;
    this.http.get(url1, {responseType: 'text'})
    .subscribe(
      data1 => {
        let parse1: any[] = this.papa.parse(data1, {header: true}).data;
        let scaled1 = this.rescale(parse1);
        this.http.get(url2, {responseType: 'text'})
        .subscribe(
          data2 => {
            let parse2: any[] = this.papa.parse(data2, {header: true}).data;
            let scaled2 = this.rescale(parse2);
            let output = [];
            let end = parse1.length > parse2.length ? parse2.length : parse1.length;
            for (let i = 0; i < end; i += 1) {
              let elem = scaled1[i];
              let elem2 = scaled2[i];
              let x1 = parseFloat(elem.x);
              let y1 = parseFloat(elem.y);
              let x2 = parseFloat(elem2.x);
              let y2 = parseFloat(elem2.y);
              if (Math.abs(x1 - x2) <= walk_tolerance && Math.abs(y1 - y2) <= walk_tolerance){
                elem.x = (x1 * weight + x2) / (weight + 1);
                elem.y = (y1 * weight + y2) / (weight + 1);
              } else {
                elem.x = x1;
                elem.y = y1;
              }
              output.push(elem);
            }
            this.mapData(output);
          },
          error => {
            console.log(error);
          }
        );

      },
      error => {
        console.log(error);
      }
    );
  }

  mapData(parsed){
    this.x = [];
    this.y = [];
    this.name = [];
    this.color = [];
    let samplesize = parsed.length > this.displayNum ? this.displayNum : parsed.length;
    let d = this.getRandomSubarray(parsed, samplesize);
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
    this.buildGraph()
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

  getGraphName(){
    switch (this.selectedBtn) {
      case "pca":
        return "Principal Component Analysis";
      case "tsne":
        return "T-Distributed Stochastic Neighbor Embedding";
      case "sernn":
        return "Spectral Embedding - K Nearest Neighbors";
      case "blend":
        return "Blended Algorithm";
    }
  }

  getGraphData(){
    this.http.get(this.dataUrl, {responseType: 'text'})
    .subscribe(
      data => {
        let parsed = this.papa.parse(data, {header: true});
        this.mapData(parsed.data);
      },
      error => {
        console.log(error);
      }
    );
  }

  updateAlgorithm(event){
    switch (event.value) {
      case "pca":
        this.dataUrl = '../assets/data/PCA2dGraphPoints.csv';
        break;
      case "tsne":
        this.dataUrl = '../assets/data/TSNE2dGraphPoints.csv';
        break;
      case "sernn":
        this.dataUrl = '../assets/data/SpectralEmbeddingNN2dGraphPoints.csv';
        break;
      case "serbf":
        this.dataUrl = '../assets/data/SpectralEmbeddingRBF2dGraphPoints.csv';
        break;
      default:
        this.dataUrl = ""
    }
    this.selectedBtn = event.value;
    if (event.value == 'blend'){
      this.buildAvg('../assets/data/TSNE2dGraphPoints.csv','../assets/data/SpectralEmbeddingRBF2dGraphPoints.csv');
    } else {
      this.getGraphData();
    }
  }

  rescale(data){
    let x: number[] = [];
    let y: number[] = [];
    let xMin = 0;
    let xMax = 0;
    let yMax = 0;
    let yMin = 0;
    for (let elem of data){
      let x_float : number = parseFloat(elem.x);
      let y_float : number = parseFloat(elem.y);
      if (x_float < xMin) { xMin = x_float; }
      if (y_float < yMin) { yMin = y_float; }
      if (x_float < xMax) { yMax = x_float; }
      if (y_float < yMax) { yMax = y_float; }
      x.push(x_float);
      y.push(y_float);
    }
    for (let i = 0; i < data.length; i += 1){
      data[i].x = (x[i] - xMin) / (xMax - xMin);
      data[i].y = (y[i] - yMin) / (yMax - yMin);
    }
    return data;
  }

  onSampleChange(event) {
    this.sampleSizeEmitter.emit();
  }

  buildGraph(){
    let marker: any = {
      color: this.color,
      line: {
        color: "#00000055",
        width: 1
      },
      size: 7,
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
      autosize: true,
      height: 800,
      title: this.getGraphName() + " - " + this.displayNum + " samples"
    };

  }
}
