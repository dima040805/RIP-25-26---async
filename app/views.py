from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import time
import random
import requests
from concurrent import futures
import math

# Конфигурация
MAIN_SERVICE_URL = "http://localhost:8080/api/v1"
AUTH_TOKEN = "secret123"  # Токен для авторизации

executor = futures.ThreadPoolExecutor(max_workers=5)

def calculate_planet_radius_single(research_id, planet_id, star_radius, planet_shine):
    """Асинхронное вычисление радиуса ОДНОЙ планеты"""
    try:
        calculation_time = random.randint(5, 10)
        print(f"Starting calculation for research {research_id}, planet {planet_id} - will take {calculation_time} seconds")
        time.sleep(calculation_time)

        if planet_shine and planet_shine > 0:
            radius_km = int(star_radius * math.sqrt(planet_shine / 100))
            success = True
            print(f"Calculation successful: planet {planet_id}, radius = {radius_km} km")
        else:
            radius_km = 0
            success = False
            print(f"Calculation failed: invalid planet_shine = {planet_shine}")
        
        return {
            "research_id": research_id,
            "planet_id": planet_id,
            "radius_km": radius_km,
            "success": success,
            "calculation_time": calculation_time
        }
    except Exception as e:
        print(f"Error in calculation for planet {planet_id}: {e}")
        return {
            "research_id": research_id,
            "planet_id": planet_id,
            "radius_km": 0,
            "success": False,
            "error": str(e)
        }

def send_calculation_result(task):
    """Колбэк для отправки результата ОДНОГО радиуса в основной сервис"""
    try:
        result = task.result()
        print(f"Sending radius calculation for research {result['research_id']}, planet {result['planet_id']}: {result['radius_km']} km")
        
        if result['success']:
            update_url = f"{MAIN_SERVICE_URL}/research/{result['research_id']}/radius"
            
            payload = {
                "planet_id": result["planet_id"],
                "planet_radius": result["radius_km"],
            }
            
            headers = {
                "Authorization": AUTH_TOKEN,
                "Content-Type": "application/json"
            }
            
            response = requests.put(update_url, json=payload, headers=headers, timeout=10)
            
            print(f"Response from main service for planet {result['planet_id']}: {response.status_code}")
            if response.status_code == 200:
                print(f"Successfully updated radius for planet {result['planet_id']}")
            else:
                print(f"Failed to update planet {result['planet_id']}: {response.text}")
        else:
            print(f"Calculation failed for planet {result['planet_id']}, not sending result")
        
    except Exception as e:
        print(f"Error sending calculation result for planet: {e}")

@api_view(['POST'])
def calculate_radius(request):
    required_fields = ["research_id", "planet_id", "star_radius", "planet_shine"]
    
    if all(field in request.data for field in required_fields):   
        research_id = request.data["research_id"]
        planet_id = request.data["planet_id"] 
        star_radius = request.data["star_radius"]
        planet_shine = request.data["planet_shine"]
        
        print(f"Received SINGLE planet calculation request: research={research_id}, planet={planet_id}, star_radius={star_radius}, shine={planet_shine}")
        
        # Запуск асинхронной задачи для ОДНОЙ планеты
        task = executor.submit(
            calculate_planet_radius_single, 
            research_id, 
            planet_id, 
            star_radius,
            planet_shine
        )
        task.add_done_callback(send_calculation_result)
        
        return Response(
            {
                "message": "Single planet radius calculation started", 
                "research_id": research_id,
                "planet_id": planet_id,
                "estimated_time": "5-10 seconds"
            },
            status=status.HTTP_202_ACCEPTED
        )
    
    return Response(
        {"error": "research_id, planet_id, star_radius and planet_shine are required"}, 
        status=status.HTTP_400_BAD_REQUEST
    )

@api_view(['POST'])
def calculate_research_radii(request):
    """Запуск расчета радиусов для всех планет в исследовании"""
    if "research_id" in request.data:   
        research_id = request.data["research_id"]
        
        print(f"Received batch calculation request for research {research_id}")
        
        return Response(
            {
                "message": "Batch radius calculation started", 
                "research_id": research_id,
                "note": "In real implementation, this would fetch research data and calculate all planets"
            },
            status=status.HTTP_202_ACCEPTED
        )
    
    return Response(
        {"error": "research_id is required"}, 
        status=status.HTTP_400_BAD_REQUEST
    )

@api_view(['GET'])
def health_check(request):
    """Проверка здоровья сервиса"""
    return Response({"status": "healthy", "service": "async-radius-calculator"}, status=status.HTTP_200_OK)